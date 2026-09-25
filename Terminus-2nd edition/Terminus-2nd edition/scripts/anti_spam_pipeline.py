#!/usr/bin/env python3
"""Multi-signal anti-templated pipeline for Terminus tasks.

Flow:
  Extract Metadata → Normalization → Embedding → Nearest Neighbors
  → Multi-Signal Similarity → Weighted Score → LLM/Heuristic Judge → Verdict

Used by scripts/terminus_anti_spam_check.py (pack_zip gate).
"""
from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "jobs-local" / "anti-spam-index.json"

# Weighted multi-signal blend (must sum to 1.0)
SIGNAL_WEIGHTS = {
    "semantic": 0.35,
    "bug_type": 0.20,
    "file_path": 0.15,
    "test_pattern": 0.15,
    "solution_pattern": 0.15,
}

VERDICT_FAIL = 0.85
VERDICT_WARN = 0.65

# Maps checker blockers → shared/unacceptable-task-classes.mdc labels.
ALL_UNACCEPTABLE_CLASSES = (
    "TEMPLATED",
    "COPY",
    "DUPLICATE",
    "FAMILY",
    "SAME_LANE",
    "SIBLING",
    "FABRICATED",
    "SYNTHETIC",
)


def classify_unacceptable_classes(
    *,
    blockers: Iterable[str],
    warnings: Iterable[str],
    similarity: float = 0.0,
    shared_family_neighbor: bool = False,
    similarity_fail: float | None = None,
) -> list[str]:
    """Derive never-accept class tags from anti-spam blockers (similarity classes only)."""
    fail_at = VERDICT_FAIL if similarity_fail is None else similarity_fail
    blob = " ".join(blockers).lower()
    warn_blob = " ".join(warnings).lower()
    classes: list[str] = []
    if (
        "templated risk" in blob
        or "idea similarity blocked" in blob
        or similarity > fail_at
    ):
        classes.append("TEMPLATED")
    if "family saturation" in blob:
        classes.extend(["FAMILY", "SAME_LANE"])
    if "templated risk" in blob and "same family" in blob:
        classes.append("SIBLING")
    elif shared_family_neighbor and similarity >= VERDICT_WARN:
        classes.append("SIBLING")
    if "slug already exists" in blob or "near-duplicate slug" in blob:
        classes.append("DUPLICATE")
    if similarity >= fail_at and "different family tags" not in warn_blob:
        classes.append("COPY")
    out: list[str] = []
    for label in ALL_UNACCEPTABLE_CLASSES:
        if label in classes and label not in out:
            out.append(label)
    return out

# Ideas phase only (stricter — before any tasks/<name>/ exists). Pack/post-create keep VERDICT_* above.
IDEA_VERDICT_FAIL = 0.10  # block proposed idea when weighted similarity > 0.10
IDEA_AUTO_CREATE_SIM = 0.0  # auto-start @CREATE when weighted == 0.0 and no slug/family blockers

PATH_CANON = re.compile(r"/app(?:/[A-Za-z0-9_.\-]+)+")
MD_NOISE = re.compile(r"[#*`>\[\](){}|]")
WS = re.compile(r"\s+")
TAGS_RE = re.compile(r"tags\s*=\s*\[(.*?)\]", re.DOTALL)
TEST_DEF_RE = re.compile(r"def (test_[a-zA-Z0-9_]+)\([^)]*\):\s*(?:\"\"\"(.*?)\"\"\"|'\'\'(.*?)\'\'\')?", re.S)
BUG_HINTS = (
    "checksum",
    "rollback",
    "idempot",
    "replay",
    "duplicate",
    "staging",
    "witness",
    "merge",
    "decode",
    "parse",
    "validate",
    "export",
    "ingest",
    "sqlite",
    "transaction",
    "ordering",
    "gap",
    "coalesce",
    "canonical",
    "envelope",
    "crc",
    "timestamp",
    "timezone",
    "pagination",
    "quarantine",
)


@dataclass
class TaskMetadata:
    slug: str
    instruction_raw: str = ""
    instruction_norm: str = ""
    files_touched: list[str] = field(default_factory=list)
    bug_categories: list[str] = field(default_factory=list)
    expected_behavior: str = ""
    test_descriptions: list[str] = field(default_factory=list)
    test_names: list[str] = field(default_factory=list)
    solution_summary: str = ""
    solution_files: list[str] = field(default_factory=list)
    key_concepts: list[str] = field(default_factory=list)
    tags: tuple[str, ...] = ()


@dataclass
class SignalScores:
    semantic: float = 0.0
    bug_type: float = 0.0
    file_path: float = 0.0
    test_pattern: float = 0.0
    solution_pattern: float = 0.0

    @property
    def weighted(self) -> float:
        total = 0.0
        for key, weight in SIGNAL_WEIGHTS.items():
            total += weight * getattr(self, key, 0.0)
        return round(total, 3)


@dataclass
class JudgeResult:
    same_objective: bool = False
    same_reasoning: bool = False
    same_fix: bool = False
    same_evaluation: bool = False
    near_copy: bool = False
    source: str = "heuristic"
    rationale: str = ""


@dataclass
class PipelineVerdict:
    slug: str
    nearest: str | None
    signals: SignalScores
    judge: JudgeResult
    status: str  # PASS | WARNING | FAIL
    weighted_score: float = 0.0
    metadata: TaskMetadata | None = None


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _list_env_files(env_dir: Path) -> list[str]:
    if not env_dir.is_dir():
        return []
    skip = {".git", "node_modules", "target", "dist", "build", "__pycache__", ".pytest_cache", "vendor"}
    out: list[str] = []
    for root, dirs, files in os.walk(env_dir):
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            if name.endswith((".pyc", ".log", ".o", ".a")):
                continue
            rel = Path(root).relative_to(env_dir) / name
            out.append(str(rel).replace("\\", "/"))
    return sorted(out)


def _parse_tags(toml_text: str) -> tuple[str, ...]:
    m = TAGS_RE.search(toml_text)
    if not m:
        return ()
    return tuple(sorted(re.findall(r'"([^"]+)"', m.group(1))))


def _infer_bug_categories(text: str, tags: Iterable[str]) -> list[str]:
    blob = " ".join(tags) + " " + text.lower()
    found = [hint for hint in BUG_HINTS if hint in blob]
    return sorted(set(found))


def _extract_test_info(test_py: Path) -> tuple[list[str], list[str]]:
    content = _read_text(test_py)
    names: list[str] = []
    descriptions: list[str] = []
    for m in TEST_DEF_RE.finditer(content):
        names.append(m.group(1))
        doc = (m.group(2) or m.group(3) or "").strip()
        if doc:
            descriptions.append(doc.splitlines()[0][:200])
    if not names:
        names = re.findall(r"def (test_[a-zA-Z0-9_]+)\(", content)
    return names, descriptions


def _summarize_solution(task_dir: Path) -> tuple[str, list[str]]:
    sol_files: list[str] = []
    for pattern in ("solution/files", "solution/patches", "solution/fixed", "solution/oracle"):
        base = task_dir / pattern.replace("/", os.sep)
        if base.is_dir():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    sol_files.append(str(p.relative_to(task_dir)).replace("\\", "/"))

    parts: list[str] = []
    for rel in ("solution/solve.sh", "solution/solve1.sh"):
        sh = task_dir / rel
        if sh.is_file():
            body = _read_text(sh)
            parts.append(body[:1200])
    if task_dir.joinpath("steps").is_dir():
        for step in sorted(task_dir.glob("steps/milestone_*/solution/solve*.sh")):
            parts.append(_read_text(step)[:600])
    summary = "\n".join(parts)
    return summary, sol_files


def extract_metadata(task_dir: Path) -> TaskMetadata | None:
    if not (task_dir / "task.toml").is_file():
        return None
    slug = task_dir.name
    toml = _read_text(task_dir / "task.toml")
    tags = _parse_tags(toml)

    instructions: list[str] = []
    root_inst = task_dir / "instruction.md"
    if root_inst.is_file():
        instructions.append(_read_text(root_inst))
    for step_inst in sorted(task_dir.glob("steps/milestone_*/instruction.md")):
        instructions.append(_read_text(step_inst))

    instruction_raw = "\n\n".join(instructions)
    files_touched = _list_env_files(task_dir / "environment")

    test_names: list[str] = []
    test_descriptions: list[str] = []
    tp = task_dir / "tests" / "test_outputs.py"
    if tp.is_file():
        test_names, test_descriptions = _extract_test_info(tp)
    for mtest in sorted(task_dir.glob("steps/milestone_*/tests/test_m*.py")):
        n, d = _extract_test_info(mtest)
        test_names.extend(n)
        test_descriptions.extend(d)

    solution_summary, solution_files = _summarize_solution(task_dir)

    docs_blob = ""
    docs_dir = task_dir / "environment" / "docs"
    if docs_dir.is_dir():
        for doc in sorted(docs_dir.glob("*.md"))[:5]:
            docs_blob += _read_text(doc)[:800]

    expected = instruction_raw[:1500]
    if docs_blob:
        expected = (expected + "\n" + docs_blob)[:2500]

    bug_categories = _infer_bug_categories(
        instruction_raw + " " + " ".join(test_descriptions) + " " + solution_summary,
        tags,
    )

    meta = TaskMetadata(
        slug=slug,
        instruction_raw=instruction_raw,
        files_touched=files_touched,
        bug_categories=bug_categories,
        expected_behavior=expected,
        test_descriptions=test_descriptions,
        test_names=test_names,
        solution_summary=solution_summary,
        solution_files=solution_files,
        tags=tags,
    )
    meta.instruction_norm, meta.key_concepts = normalize_text(instruction_raw)
    return meta


def canonicalize_paths(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        parts = m.group(0).split("/")
        if len(parts) <= 2:
            return "/app"
        return "/app/" + "/".join(f"<p{i}>" for i in range(1, len(parts) - 1)) + "/" + parts[-1]

    return PATH_CANON.sub(repl, text)


def normalize_text(text: str) -> tuple[str, list[str]]:
    t = text.lower()
    t = canonicalize_paths(t)
    t = MD_NOISE.sub(" ", t)
    t = WS.sub(" ", t).strip()
    tokens = [w for w in re.findall(r"[a-z0-9_\-]{3,}", t) if w not in STOPWORDS]
    concepts = sorted({w for w in tokens if len(w) > 4 or w in BUG_HINTS})[:40]
    return t, concepts


STOPWORDS = frozenset(
    """
    the and for with that this from your must when into each also only have will
    should than then them they their there these those using used use under over
    after before about through while where which what were been being does done
    """.split()
)


def tokenize(text: str) -> list[str]:
    norm, _ = normalize_text(text)
    return re.findall(r"[a-z0-9_\-]{3,}", norm)


def _tf_vector(tokens: list[str], vocab: dict[str, int]) -> list[float]:
    counts = Counter(tokens)
    total = sum(counts.values()) or 1
    vec = [0.0] * len(vocab)
    for term, cnt in counts.items():
        if term in vocab:
            vec[vocab[term]] = cnt / total
    return vec


def _idf(documents: list[list[str]]) -> dict[str, float]:
    df: Counter[str] = Counter()
    for doc in documents:
        for term in set(doc):
            df[term] += 1
    n = len(documents) or 1
    return {term: math.log((1 + n) / (1 + df[term])) + 1.0 for term in df}


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def build_embedding_text(meta: TaskMetadata) -> str:
    parts = [
        meta.instruction_norm,
        meta.expected_behavior,
        " ".join(meta.test_descriptions),
        " ".join(meta.bug_categories),
        meta.solution_summary[:800],
    ]
    return " ".join(p for p in parts if p)


def build_corpus_index(all_meta: dict[str, TaskMetadata]) -> dict[str, Any]:
    slugs = sorted(all_meta.keys())
    docs = [tokenize(build_embedding_text(all_meta[s])) for s in slugs]
    idf = _idf(docs)
    vocab_terms = sorted(idf.keys())
    vocab = {t: i for i, t in enumerate(vocab_terms)}

    vectors: dict[str, list[float]] = {}
    for slug, tokens in zip(slugs, docs):
        tf = _tf_vector(tokens, vocab)
        vectors[slug] = [tf[i] * idf.get(term, 1.0) for i, term in enumerate(vocab_terms)]

    file_sets = {s: all_meta[s].files_touched for s in slugs}
    test_sets = {s: all_meta[s].test_names for s in slugs}
    bug_sets = {s: all_meta[s].bug_categories for s in slugs}
    sol_sets = {s: all_meta[s].solution_files for s in slugs}

    return {
        "version": 1,
        "slugs": slugs,
        "vocab_size": len(vocab),
        "vocab_terms": vocab_terms,
        "idf": idf,
        "vectors": vectors,
        "file_sets": file_sets,
        "test_sets": test_sets,
        "bug_sets": bug_sets,
        "sol_sets": sol_sets,
        "concepts": {s: all_meta[s].key_concepts for s in slugs},
    }


def embed_text(text: str, index: dict[str, Any]) -> list[float]:
    """TF-IDF vector for arbitrary text using a built corpus index."""
    vocab_terms: list[str] = index.get("vocab_terms") or []
    idf: dict[str, float] = index.get("idf") or {}
    if not vocab_terms:
        return []
    vocab = {t: i for i, t in enumerate(vocab_terms)}
    tokens = tokenize(text)
    tf = _tf_vector(tokens, vocab)
    return [tf[i] * idf.get(term, 1.0) for i, term in enumerate(vocab_terms)]


def semantic_nearest_text(
    text: str,
    index: dict[str, Any],
    *,
    exclude_slug: str | None = None,
) -> tuple[str | None, float]:
    vec = embed_text(text, index)
    if not vec:
        return None, 0.0
    best_sim = 0.0
    best_slug: str | None = None
    for other, ovec in index.get("vectors", {}).items():
        if exclude_slug and other == exclude_slug:
            continue
        sim = _cosine(vec, ovec)
        if sim > best_sim:
            best_sim = sim
            best_slug = other
    return best_slug, round(best_sim, 3)


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug[:80] or "untitled-task"


def score_idea_text(
    text: str,
    slug: str,
    index: dict[str, Any],
    all_meta: dict[str, TaskMetadata],
) -> tuple[SignalScores, str | None]:
    """Idea-stage multi-signal score (no env files / tests yet)."""
    nearest, semantic = semantic_nearest_text(text, index, exclude_slug=slug)
    bug_type = 0.0
    if nearest and nearest in all_meta:
        proposed_bugs = set(_infer_bug_categories(text, ()))
        bug_type = round(
            len(proposed_bugs & set(all_meta[nearest].bug_categories))
            / max(len(proposed_bugs | set(all_meta[nearest].bug_categories)), 1),
            3,
        )
    signals = SignalScores(
        semantic=semantic,
        bug_type=bug_type,
        file_path=0.0,
        test_pattern=0.0,
        solution_pattern=0.0,
    )
    return signals, nearest


def save_index(index: dict[str, Any]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")


def load_or_build_index(all_meta: dict[str, TaskMetadata], *, rebuild: bool = False) -> dict[str, Any]:
    if not rebuild and INDEX_PATH.is_file():
        try:
            cached = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            if (
                cached.get("slugs")
                and set(cached["slugs"]) == set(all_meta.keys())
                and cached.get("vocab_terms")
                and cached.get("idf")
            ):
                return cached
        except (json.JSONDecodeError, OSError):
            pass
    index = build_corpus_index(all_meta)
    save_index(index)
    return index


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _basename_pattern(paths: Iterable[str]) -> set[str]:
    out: set[str] = set()
    for p in paths:
        parts = Path(p).parts
        if parts:
            out.add(parts[0])
            if len(parts) > 1:
                out.add(Path(p).suffix or parts[-1].split(".")[-1])
    return out


def _test_pattern_set(names: list[str]) -> set[str]:
    out: set[str] = set()
    for n in names:
        base = re.sub(r"_\d+$", "", n)
        base = re.sub(r"test_", "", base)
        for chunk in base.split("_"):
            if len(chunk) > 3:
                out.add(chunk)
    return out


def _solution_pattern(meta: TaskMetadata) -> set[str]:
    patterns: set[str] = set()
    for f in meta.solution_files:
        patterns.add(Path(f).suffix)
        patterns.add(Path(f).name)
    for line in meta.solution_summary.splitlines():
        line = line.strip()
        if line.startswith(("cp ", "mv ", "cargo ", "go ", "npm ", "make ", "patch")):
            patterns.add(line.split()[0])
    return patterns


def compute_signals(a: TaskMetadata, b: TaskMetadata, index: dict[str, Any]) -> SignalScores:
    va = index["vectors"].get(a.slug, [])
    vb = index["vectors"].get(b.slug, [])
    semantic = round(_cosine(va, vb), 3) if va and vb else 0.0

    bug_type = round(_jaccard(set(a.bug_categories), set(b.bug_categories)), 3)

    file_path = round(
        _jaccard(_basename_pattern(a.files_touched), _basename_pattern(b.files_touched)),
        3,
    )

    test_pattern = round(
        _jaccard(_test_pattern_set(a.test_names), _test_pattern_set(b.test_names)),
        3,
    )

    solution_pattern = round(_jaccard(_solution_pattern(a), _solution_pattern(b)), 3)

    return SignalScores(
        semantic=semantic,
        bug_type=bug_type,
        file_path=file_path,
        test_pattern=test_pattern,
        solution_pattern=solution_pattern,
    )


def retrieve_nearest_neighbors(
    slug: str,
    index: dict[str, Any],
    *,
    top_k: int = 5,
) -> list[tuple[str, float]]:
    vec = index["vectors"].get(slug)
    if not vec:
        return []
    scores: list[tuple[str, float]] = []
    for other, ovec in index["vectors"].items():
        if other == slug:
            continue
        scores.append((other, round(_cosine(vec, ovec), 3)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def heuristic_judge(signals: SignalScores, weighted: float) -> JudgeResult:
    same_objective = signals.semantic >= 0.55 and weighted >= 0.60
    same_reasoning = signals.bug_type >= 0.50 and signals.test_pattern >= 0.45
    same_fix = signals.solution_pattern >= 0.55
    same_evaluation = signals.test_pattern >= 0.60 and signals.file_path >= 0.50
    near_copy = (
        weighted >= VERDICT_FAIL
        or (
            weighted >= 0.75
            and signals.semantic >= 0.65
            and signals.solution_pattern >= 0.50
        )
    )
    rationale = (
        f"weighted={weighted}; semantic={signals.semantic}; "
        f"bug={signals.bug_type}; test={signals.test_pattern}; sol={signals.solution_pattern}"
    )
    return JudgeResult(
        same_objective=same_objective,
        same_reasoning=same_reasoning,
        same_fix=same_fix,
        same_evaluation=same_evaluation,
        near_copy=near_copy,
        source="heuristic",
        rationale=rationale,
    )


def llm_judge(
    a: TaskMetadata,
    b: TaskMetadata,
    signals: SignalScores,
) -> JudgeResult | None:
    """Optional OpenAI-compatible judge when ANTI_SPAM_LLM=1 and API key set."""
    if os.environ.get("ANTI_SPAM_LLM", "").strip() not in ("1", "true", "yes"):
        return None
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("ANTI_SPAM_LLM_MODEL", "gpt-4o-mini")

    prompt = f"""Compare two Terminal-Bench coding tasks. Answer JSON only:
{{"same_objective":bool,"same_reasoning":bool,"same_fix":bool,"same_evaluation":bool,"near_copy":bool,"rationale":"..."}}

Task A ({a.slug}):
Instruction excerpt: {a.instruction_raw[:800]}
Bug hints: {a.bug_categories}
Tests: {a.test_names[:12]}

Task B ({b.slug}):
Instruction excerpt: {b.instruction_raw[:800]}
Bug hints: {b.bug_categories}
Tests: {b.test_names[:12]}

Automated signals: {asdict(signals)}
"""
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        data = json.loads(content)
        return JudgeResult(
            same_objective=bool(data.get("same_objective")),
            same_reasoning=bool(data.get("same_reasoning")),
            same_fix=bool(data.get("same_fix")),
            same_evaluation=bool(data.get("same_evaluation")),
            near_copy=bool(data.get("near_copy")),
            source="llm",
            rationale=str(data.get("rationale", ""))[:500],
        )
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return None


def final_verdict(judge: JudgeResult, weighted: float) -> str:
    if judge.near_copy or weighted >= VERDICT_FAIL:
        return "FAIL"
    if weighted >= VERDICT_WARN or judge.same_objective or judge.same_reasoning:
        return "WARNING"
    return "PASS"


def idea_similarity_verdict(weighted: float) -> str:
    """Ideas intake only — block when weighted > IDEA_VERDICT_FAIL (0.10)."""
    if weighted > IDEA_VERDICT_FAIL:
        return "FAIL"
    return "PASS"


def idea_should_auto_create(weighted: float, *, has_blockers: bool) -> bool:
    """True when similarity is exactly zero and no slug/family blockers."""
    return not has_blockers and weighted <= IDEA_AUTO_CREATE_SIM


def run_pipeline_for_slug(
    slug: str,
    all_meta: dict[str, TaskMetadata],
    *,
    rebuild_index: bool = False,
    use_llm: bool = False,
) -> PipelineVerdict | None:
    meta = all_meta.get(slug)
    if meta is None:
        return None

    index = load_or_build_index(all_meta, rebuild=rebuild_index)
    neighbors = retrieve_nearest_neighbors(slug, index, top_k=1)
    if not neighbors:
        return PipelineVerdict(
            slug=slug,
            nearest=None,
            signals=SignalScores(),
            judge=JudgeResult(rationale="no neighbors in corpus"),
            status="PASS",
            weighted_score=0.0,
            metadata=meta,
        )

    nearest_slug, _emb_sim = neighbors[0]
    other = all_meta[nearest_slug]
    signals = compute_signals(meta, other, index)
    weighted = signals.weighted

    judge = heuristic_judge(signals, weighted)
    if use_llm:
        llm = llm_judge(meta, other, signals)
        if llm is not None:
            judge = llm

    status = final_verdict(judge, weighted)
    return PipelineVerdict(
        slug=slug,
        nearest=nearest_slug,
        signals=signals,
        judge=judge,
        status=status,
        weighted_score=weighted,
        metadata=meta,
    )


def build_metadata_corpus(task_dirs: Iterable[Path]) -> dict[str, TaskMetadata]:
    out: dict[str, TaskMetadata] = {}
    for td in task_dirs:
        meta = extract_metadata(td)
        if meta:
            out[meta.slug] = meta
    return out


def format_pipeline_report(verdict: PipelineVerdict) -> str:
    sig = verdict.signals
    j = verdict.judge
    return (
        f"Pipeline: {verdict.status} — nearest {verdict.nearest or 'none'} "
        f"(weighted {verdict.weighted_score}) "
        f"[sem={sig.semantic} bug={sig.bug_type} path={sig.file_path} "
        f"test={sig.test_pattern} sol={sig.solution_pattern}] "
        f"judge={j.source} near_copy={j.near_copy}"
    )


def pipeline_to_dict(verdict: PipelineVerdict) -> dict[str, Any]:
    return {
        "slug": verdict.slug,
        "nearest": verdict.nearest,
        "weighted_score": verdict.weighted_score,
        "status": verdict.status,
        "signals": asdict(verdict.signals),
        "judge": asdict(verdict.judge),
        "metadata_summary": {
            "files_touched": len(verdict.metadata.files_touched) if verdict.metadata else 0,
            "test_count": len(verdict.metadata.test_names) if verdict.metadata else 0,
            "bug_categories": verdict.metadata.bug_categories if verdict.metadata else [],
            "key_concepts": verdict.metadata.key_concepts[:10] if verdict.metadata else [],
        },
    }


def _main() -> int:
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, help="Task folder path")
    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--llm-judge", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    task_dir = Path(args.task_dir).resolve()
    slug = task_dir.name
    dirs: list[Path] = []
    repo = Path(__file__).resolve().parent.parent
    for root_name in ("tasks", "pending"):
        root = repo / root_name
        if root.is_dir():
            dirs.extend(p for p in root.iterdir() if p.is_dir() and (p / "task.toml").is_file())
    acc = repo / "tasks" / "_accepted-tasks"
    if acc.is_dir():
        dirs.extend(p for p in acc.iterdir() if p.is_dir() and (p / "task.toml").is_file())
    if task_dir not in dirs:
        dirs.append(task_dir)

    all_meta = build_metadata_corpus(dirs)
    verdict = run_pipeline_for_slug(
        slug,
        all_meta,
        rebuild_index=args.rebuild_index,
        use_llm=args.llm_judge,
    )
    if verdict is None:
        print(f"ERROR: no metadata for {slug}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(pipeline_to_dict(verdict), indent=2))
    else:
        print(format_pipeline_report(verdict))
        if verdict.metadata:
            print(f"  concepts: {', '.join(verdict.metadata.key_concepts[:8]) or 'n/a'}")
            print(f"  bug_types: {', '.join(verdict.metadata.bug_categories[:8]) or 'n/a'}")
    return 0 if verdict.status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
