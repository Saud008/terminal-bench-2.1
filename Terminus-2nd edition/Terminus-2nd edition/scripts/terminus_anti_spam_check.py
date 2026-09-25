#!/usr/bin/env python3
"""Anti-spam / anti-templated gate for Terminus tasks (see anti-spam-templated-submissions.mdc).

Multi-signal pipeline (extract → normalize → embed → neighbors → judge):
  scripts/anti_spam_pipeline.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

try:
    from anti_spam_pipeline import (
        PipelineVerdict,
        build_metadata_corpus,
        classify_unacceptable_classes,
        format_pipeline_report,
        load_or_build_index,
        pipeline_to_dict,
        run_pipeline_for_slug,
    )
except ImportError:  # pragma: no cover — run from repo root or scripts/
    from scripts.anti_spam_pipeline import (  # type: ignore[no-redef]
        PipelineVerdict,
        build_metadata_corpus,
        classify_unacceptable_classes,
        format_pipeline_report,
        load_or_build_index,
        pipeline_to_dict,
        run_pipeline_for_slug,
    )

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLATFORM_FILE = REPO_ROOT / "scripts" / "platform_submissions.txt"
PACKED_FOR_UPLOAD_FILE = REPO_ROOT / "scripts" / "packed_for_upload.txt"
RULE = ".cursor/rules/engines/ENGINE_2_anti_spam.mdc"

# Sanjana standing (LOCKED): pack gate reports sim 0.0 only — block zip if > 0.
PACK_SIM_MUST_BE_ZERO = True

SPAM_SLUG_RE = re.compile(
    r"(difficulty[-_]?check|artifact|rubric[-_]?only|spam[-_]?test)",
    re.I,
)

LANGS_RE = re.compile(r"languages\s*=\s*\[(.*?)\]", re.DOTALL)
CATEGORY_RE = re.compile(r'^category\s*=\s*"([^"]+)"', re.MULTILINE)
DIFFICULTY_RE = re.compile(r'^difficulty\s*=\s*"([^"]+)"', re.MULTILINE)
FROM_RE = re.compile(r"^FROM\s+(?:--platform=[^\s]+\s+)?(\S+)", re.MULTILINE)

FamilyMatcher = Callable[[str, "Fingerprint"], bool]


def _slug_hyphen_tokens(slug: str) -> set[str]:
    """Hyphen-delimited slug segments (avoids questframe matching token frame)."""
    return {t for t in slug.split("-") if t}


def _slug_has_token(slug: str, *needles: str) -> bool:
    parts = _slug_hyphen_tokens(slug)
    return any(n in parts for n in needles)


def _slug_has_substr(slug: str, *needles: str) -> bool:
    return any(n in slug for n in needles)


FAMILY_MATCHERS: list[tuple[str, str, FamilyMatcher]] = [
    (
        "go_jsonl_sqlite",
        "Go twin CLI + JSONL/SQLite audit",
        lambda s, fp: fp.has_go
        and (
            "ingest" in s
            or "sqlite" in s
            or "quarantine" in s
            or "audit-cli" in s
            or "reconciler" in s
            or "export" in s
        ),
    ),
    (
        "custody_ledger",
        "Custody / ledger / staging rollup",
        lambda s, fp: any(x in s for x in ("custody", "ledger", "settlement", "staging"))
        and ("reconciler" in s or "ingest" in s or "rollup" in s),
    ),
    (
        "merge_cli",
        "Merge / export directory CLI",
        lambda s, fp: any(x in s for x in ("-merge", "-normalizer", "dedupe", "shard-merge"))
        or (fp.has_makefile and "merge" in s),
    ),
    (
        "game_sim",
        "Game / sim score or timing auditor",
        lambda s, fp: any(
            x in s
            for x in (
                "tetris",
                "rts-",
                "pinball",
                "scrabble",
                "racing",
                "ccg-",
                "mahjong",
                "bridge-",
                "shogi",
                "backgammon",
                "battleship",
                "cribbage",
                "bowling",
                "fighting-game",
                "doom-",
                "rally-",
                "arena-match",
                "sim-racing",
                "4x-",
                "tactics-",
                "roguelike",
                "gameserver",
                "pixelvault",
                "glyphlock",
            )
        ),
    ),
    (
        "rust_binary_decoder",
        "Rust protocol / binary decoder CLI",
        lambda s, fp: fp.has_cargo
        and _slug_has_token(
            s, "decoder", "binder", "tlv", "frame", "packet", "envelope", "hpke"
        ),
    ),
    (
        "node_api_replay",
        "Node/TS API or replay service",
        lambda s, fp: fp.has_package_json
        and any(x in s for x in ("replay", "reconcile", "order-", "prosemirror", "reservation")),
    ),
    (
        "bash_tool_audit",
        "Bash / tool-specific config audit",
        lambda s, fp: not fp.has_go
        and not fp.has_cargo
        and not fp.has_package_json
        and any(x in s for x in ("fail2ban", "udev", "auditd", "systemd", "crontab", "ansible")),
    ),
    (
        "cpp_perf_trace",
        "C++ perf / trace correlator",
        lambda s, fp: any(x in s for x in ("perfetto", "flamegraph", "valgrind", "dwarf")),
    ),
]


@dataclass
class Fingerprint:
    slug: str
    langs: tuple[str, ...] = ()
    milestone: bool = False
    has_go: bool = False
    has_cargo: bool = False
    has_package_json: bool = False
    has_makefile: bool = False
    category: str | None = None
    difficulty: str | None = None
    test_count: int = 0
    has_reference_impl: bool = False
    has_assert_matches_reference: bool = False
    has_tb3: bool = False
    has_subprocess: bool = False
    rebuild_in_test_sh: bool = False
    env_meaningful_files: int = 0
    primary_from: str | None = None
    families: tuple[str, ...] = ()


@dataclass
class CheckResult:
    slug: str
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    families: list[str] = field(default_factory=list)
    family_counts: dict[str, int] = field(default_factory=dict)
    nearest: str | None = None
    similarity: float = 0.0
    structural_diffs: list[str] = field(default_factory=list)
    on_platform: bool | None = None
    templated_risk: str = "Low"
    pipeline: PipelineVerdict | None = None
    unacceptable_classes: list[str] = field(default_factory=list)


def _parse_langs(text: str) -> tuple[str, ...]:
    m = LANGS_RE.search(text)
    if not m:
        return ()
    return tuple(sorted(re.findall(r'"([^"]+)"', m.group(1))))


def fingerprint_task(task_dir: Path) -> Fingerprint | None:
    if not task_dir.is_dir():
        return None
    slug = task_dir.name
    if slug.startswith("_") or slug == "tasksss":
        return None

    toml = task_dir / "task.toml"
    if not toml.is_file():
        return None

    toml_text = toml.read_text(encoding="utf-8", errors="replace")
    env = task_dir / "environment"

    fp = Fingerprint(slug=slug, langs=_parse_langs(toml_text))
    fp.milestone = (task_dir / "steps").is_dir()
    fp.has_go = (env / "go.mod").is_file() or (env / "go.sum").is_file()
    fp.has_cargo = (env / "Cargo.toml").is_file()
    fp.has_package_json = (env / "package.json").is_file()
    fp.has_makefile = (env / "Makefile").is_file()

    cat_m = CATEGORY_RE.search(toml_text)
    if cat_m:
        fp.category = cat_m.group(1)
    diff_m = DIFFICULTY_RE.search(toml_text)
    if diff_m:
        fp.difficulty = diff_m.group(1)

    dockerfile = env / "Dockerfile"
    if dockerfile.is_file():
        df = dockerfile.read_text(encoding="utf-8", errors="replace")
        fm = FROM_RE.search(df)
        if fm:
            fp.primary_from = fm.group(1).split("@")[0]

    test_py = task_dir / "tests" / "test_outputs.py"
    if test_py.is_file():
        content = test_py.read_text(encoding="utf-8", errors="replace")
        fp.test_count = content.count("def test_")
        fp.has_reference_impl = bool(re.search(r"reference_|_reference|Reference", content))
        fp.has_assert_matches_reference = "assert_matches_reference" in content
        fp.has_tb3 = "TB3_" in content
        fp.has_subprocess = "subprocess" in content

    test_sh = task_dir / "tests" / "test.sh"
    if test_sh.is_file():
        sh = test_sh.read_text(encoding="utf-8", errors="replace")
        fp.rebuild_in_test_sh = any(
            x in sh for x in ("cargo build", "go build", "npm run build", "rebuild-", "make ")
        )

    if env.is_dir():
        skip = {".git", "node_modules", "target", "dist", "build", "__pycache__", ".pytest_cache"}
        count = 0
        for root, dirs, files in os.walk(env):
            dirs[:] = [d for d in dirs if d not in skip]
            for f in files:
                if f.endswith((".pyc", ".log")):
                    continue
                count += 1
        fp.env_meaningful_files = count

    families: list[str] = []
    for fid, _label, matcher in FAMILY_MATCHERS:
        if matcher(slug, fp):
            families.append(fid)
    fp.families = tuple(families)
    return fp


def slug_token_jaccard(a: str, b: str) -> float:
    ta = {t for t in a.split("-") if len(t) > 2}
    tb = {t for t in b.split("-") if len(t) > 2}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def similarity(a: Fingerprint, b: Fingerprint) -> float:
    if a.slug == b.slug:
        return 1.0

    slug_sim = slug_token_jaccard(a.slug, b.slug)
    # Standing default: only near-duplicate slugs (≥0.72 token jaccard) compare harness.
    # Shared family tags or generic slug words (rollup, certificate, replay) alone → sim 0.
    if slug_sim < 0.72:
        return 0.0

    shared_families = set(a.families) & set(b.families)

    score = 0.0
    weight = 0.0

    def add(match: bool, w: float = 1.0) -> None:
        nonlocal score, weight
        weight += w
        if match:
            score += w

    add(a.langs == b.langs, 2.0)
    add(a.has_go == b.has_go)
    add(a.has_cargo == b.has_cargo)
    add(a.has_package_json == b.has_package_json)
    add(a.milestone == b.milestone)
    add(a.has_reference_impl == b.has_reference_impl, 1.5)
    add(a.has_assert_matches_reference == b.has_assert_matches_reference, 1.5)
    add(a.has_tb3 == b.has_tb3)
    add(a.rebuild_in_test_sh == b.rebuild_in_test_sh)
    add(a.has_subprocess == b.has_subprocess)

    if a.test_count and b.test_count:
        add(abs(a.test_count - b.test_count) <= 3, 1.0)

    add(bool(shared_families), 2.0 if shared_families else 0.0)

    if a.env_meaningful_files and b.env_meaningful_files:
        ratio = min(a.env_meaningful_files, b.env_meaningful_files) / max(
            a.env_meaningful_files, b.env_meaningful_files
        )
        add(ratio >= 0.6, 1.0)

    base = score / weight if weight else 0.0
    # Down-weight harness-only similarity when slugs share no domain tokens.
    return round(base * (0.35 + 0.65 * slug_sim), 3)


def structural_diffs(a: Fingerprint, b: Fingerprint) -> list[str]:
    diffs: list[str] = []
    if a.langs != b.langs:
        diffs.append(f"languages {a.langs} vs {b.langs}")
    if a.has_go != b.has_go:
        diffs.append(f"Go stack {'yes' if a.has_go else 'no'} vs {'yes' if b.has_go else 'no'}")
    if a.has_cargo != b.has_cargo:
        diffs.append(
            f"Rust stack {'yes' if a.has_cargo else 'no'} vs {'yes' if b.has_cargo else 'no'}"
        )
    if a.has_package_json != b.has_package_json:
        diffs.append(
            f"Node stack {'yes' if a.has_package_json else 'no'} vs {'yes' if b.has_package_json else 'no'}"
        )
    if a.milestone != b.milestone:
        diffs.append(f"milestone {'yes' if a.milestone else 'no'} vs {'yes' if b.milestone else 'no'}")
    if a.has_reference_impl != b.has_reference_impl:
        diffs.append("reference impl pattern differs")
    if a.has_tb3 != b.has_tb3:
        diffs.append("TB3_* probe pattern differs")
    if abs(a.test_count - b.test_count) > 5:
        diffs.append(f"test count {a.test_count} vs {b.test_count}")
    if set(a.families) != set(b.families):
        diffs.append(f"family tags {a.families} vs {b.families}")
    if a.primary_from and b.primary_from and a.primary_from != b.primary_from:
        diffs.append(f"Docker base {a.primary_from} vs {b.primary_from}")
    return diffs[:6]


def load_platform_slugs(path: Path | None) -> set[str]:
    if path is None or not path.is_file():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line.split()[0])
    return out


def load_all_submission_slugs(platform_file: Path | None) -> set[str]:
    """Platform export + slugs auto-registered on pack (pending upload)."""
    slugs = load_platform_slugs(platform_file)
    slugs |= load_platform_slugs(PACKED_FOR_UPLOAD_FILE)
    return slugs


def register_packed_slug(slug: str) -> tuple[bool, str]:
    """Append slug to packed_for_upload.txt after successful pack_zip."""
    slug = slug.strip()
    if not slug or SPAM_SLUG_RE.search(slug):
        return False, f"invalid slug: {slug}"

    known = load_all_submission_slugs(DEFAULT_PLATFORM_FILE)
    if slug in known:
        return False, f"already tracked: {slug}"

    PACKED_FOR_UPLOAD_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_file = not PACKED_FOR_UPLOAD_FILE.is_file() or PACKED_FOR_UPLOAD_FILE.stat().st_size == 0
    with PACKED_FOR_UPLOAD_FILE.open("a", encoding="utf-8") as fh:
        if new_file:
            fh.write(
                "# Auto-added by ./scripts/pack_zip.sh — packed locally, pending platform upload.\n"
                "# After platform accepts, refresh scripts/platform_submissions.txt from export.\n"
            )
        fh.write(f"{slug}\n")
    return True, f"registered packed: {slug}"


def locate_task_dir(slug: str) -> Path | None:
    for candidate in (
        REPO_ROOT / "pending" / slug,
        REPO_ROOT / "tasks" / slug,
    ):
        if candidate.is_dir() and (candidate / "task.toml").is_file():
            return candidate
    return None


def list_task_dirs(tasks_root: Path) -> list[Path]:
    """Active corpus under tasks/ only (pending/ is separate — not nested under tasks/)."""
    if not tasks_root.is_dir():
        return []
    dirs: list[Path] = []
    for p in sorted(tasks_root.iterdir()):
        if p.is_dir() and not p.name.startswith("_") and p.name != "tasksss":
            if (p / "task.toml").is_file():
                dirs.append(p)
    return dirs


def list_pending_dirs() -> list[Path]:
    root = REPO_ROOT / "pending"
    if not root.is_dir():
        return []
    return sorted(
        p for p in root.iterdir() if p.is_dir() and (p / "task.toml").is_file()
    )


def list_accepted_dirs() -> list[Path]:
    root = REPO_ROOT / "tasks" / "_accepted-tasks"
    if not root.is_dir():
        return []
    return sorted(
        p for p in root.iterdir() if p.is_dir() and (p / "task.toml").is_file()
    )


def all_corpus_task_dirs() -> list[Path]:
    """Historical task database: active tasks + pending + accepted corpus."""
    seen: set[str] = set()
    dirs: list[Path] = []
    for td in list_task_dirs(REPO_ROOT / "tasks") + list_pending_dirs() + list_accepted_dirs():
        if td.name not in seen:
            seen.add(td.name)
            dirs.append(td)
    return dirs


def build_all_metadata(*, rebuild_index: bool = False) -> dict:
    meta = build_metadata_corpus(all_corpus_task_dirs())
    if rebuild_index:
        load_or_build_index(meta, rebuild=True)
    return meta


def zip_only_spam(tasksubmit: Path) -> list[str]:
    bad: list[str] = []
    if not tasksubmit.is_dir():
        return bad
    for z in tasksubmit.glob("*.zip"):
        slug = z.stem
        if locate_task_dir(slug) is not None:
            continue
        if (REPO_ROOT / "tasks" / "_accepted-tasks" / slug).is_dir():
            continue
        bad.append(slug)
    return bad


def same_day_zip_clusters(tasksubmit: Path, min_count: int = 5) -> list[tuple[str, int, list[str]]]:
    by_day: dict[str, list[str]] = defaultdict(list)
    if not tasksubmit.is_dir():
        return []
    for z in tasksubmit.glob("*.zip"):
        day = datetime.fromtimestamp(z.stat().st_mtime).strftime("%Y-%m-%d")
        by_day[day].append(z.stem)
    return [(day, len(names), sorted(names)) for day, names in sorted(by_day.items()) if len(names) >= min_count]


def family_label(fid: str) -> str:
    for f, label, _ in FAMILY_MATCHERS:
        if f == fid:
            return label
    return fid


def _apply_pipeline_verdict(
    result: CheckResult,
    pipeline: PipelineVerdict | None,
    *,
    legacy_sim: float = 0.0,
) -> None:
    if pipeline is None:
        return
    result.pipeline = pipeline

    sig = pipeline.signals
    if pipeline.status == "FAIL":
        result.blockers.append(
            f"near-copy pipeline: weighted {pipeline.weighted_score:.2f} to "
            f"{pipeline.nearest} (sem={sig.semantic}, test={sig.test_pattern}, "
            f"sol={sig.solution_pattern})"
        )
    elif pipeline.status == "WARNING":
        result.warnings.append(
            f"pipeline WARNING: weighted {pipeline.weighted_score:.2f} to "
            f"{pipeline.nearest} — judge {pipeline.judge.source} "
            f"near_copy={pipeline.judge.near_copy}"
        )

    # Unrelated tasks (legacy fingerprint sim 0): keep displayed sim at 0 — do not
    # inflate from pipeline harness overlap (same rule as similarity() early return).
    if legacy_sim == 0.0:
        return

    if pipeline.nearest:
        if result.nearest is None or pipeline.weighted_score > result.similarity:
            result.nearest = pipeline.nearest
        result.similarity = round(max(result.similarity, pipeline.weighted_score), 3)


def check_one(
    slug: str,
    all_fps: dict[str, Fingerprint],
    platform: set[str],
    *,
    strict: bool = False,
    similarity_fail: float = 0.85,
    similarity_warn: float = 0.75,
    family_saturation: int = 3,
    all_meta: dict | None = None,
    rebuild_index: bool = False,
    use_llm: bool = False,
) -> CheckResult:
    fp = all_fps.get(slug)
    if fp is None:
        return CheckResult(
            slug=slug,
            status="FAIL",
            blockers=[f"no task dir or task.toml: tasks/{slug}/"],
        )

    result = CheckResult(
        slug=slug,
        status="PASS",
        families=list(fp.families),
        on_platform=slug in platform if platform else None,
    )

    if SPAM_SLUG_RE.search(slug):
        result.blockers.append(f"spam slug pattern in name ({SPAM_SLUG_RE.pattern})")

    family_counts: dict[str, int] = defaultdict(int)
    for other_fp in all_fps.values():
        for fam in other_fp.families:
            family_counts[fam] += 1
    result.family_counts = dict(family_counts)

    for fam in fp.families:
        cnt = family_counts.get(fam, 0)
        if cnt >= family_saturation:
            result.blockers.append(
                f"family saturation: {fam} ({family_label(fam)}) has {cnt} tasks in tasks/ "
                f"(max {family_saturation - 1} before block)"
            )

    best_sim = 0.0
    best_slug: str | None = None
    for other_slug, other_fp in all_fps.items():
        if other_slug == slug:
            continue
        sim = similarity(fp, other_fp)
        if sim > best_sim:
            best_sim = sim
            best_slug = other_slug

    result.nearest = best_slug
    result.similarity = round(best_sim, 3)
    if best_slug:
        result.structural_diffs = structural_diffs(fp, all_fps[best_slug])

    shared_with_nearest = bool(
        best_slug and set(fp.families) & set(all_fps[best_slug].families)
    )

    if best_sim >= similarity_fail and shared_with_nearest:
        result.blockers.append(
            f"templated risk: similarity {best_sim:.2f} to tasks/{best_slug} in same family"
        )
    elif best_sim >= similarity_fail:
        result.warnings.append(
            f"high structural similarity {best_sim:.2f} to tasks/{best_slug} (different family tags)"
        )
    elif best_sim >= similarity_warn:
        result.warnings.append(f"moderate similarity {best_sim:.2f} to tasks/{best_slug}")

    if len(result.structural_diffs) < 2 and best_sim >= similarity_warn:
        result.warnings.append(
            f"fewer than 2 structural diffs vs nearest ({len(result.structural_diffs)} listed)"
        )

    if all_meta is not None:
        pipeline = run_pipeline_for_slug(
            slug,
            all_meta,
            rebuild_index=rebuild_index,
            use_llm=use_llm,
        )
        _apply_pipeline_verdict(result, pipeline, legacy_sim=result.similarity)

    if result.blockers:
        result.templated_risk = "High"
    elif best_sim >= 0.8 or any(family_counts.get(f, 0) >= 2 for f in fp.families):
        result.templated_risk = "Medium"
    else:
        result.templated_risk = "Low"

    if strict and result.warnings:
        result.blockers.extend([f"(strict) {w}" for w in result.warnings])
        result.warnings = []

    if PACK_SIM_MUST_BE_ZERO and result.similarity > 0.0:
        neighbor = result.nearest or "unknown"
        result.blockers.append(
            f"similarity must be 0.0 before zip (got {result.similarity:.3f} vs {neighbor}); "
            "fix task in place — remove false family tag, differentiate slug/stack/harness "
            "(see shared/sanjana-standing-requirements.mdc §K)"
        )

    result.status = "FAIL" if result.blockers else ("WARN" if result.warnings else "PASS")
    result.unacceptable_classes = classify_unacceptable_classes(
        blockers=result.blockers,
        warnings=result.warnings,
        similarity=result.similarity,
        shared_family_neighbor=shared_with_nearest,
    )
    return result


def format_line(result: CheckResult, *, include_pipeline: bool = False) -> str:
    neighbor = result.nearest or "none"
    diffs = "; ".join(result.structural_diffs[:2]) if result.structural_diffs else "n/a"
    pipeline_bit = ""
    if include_pipeline and result.pipeline is not None:
        pipeline_bit = f" | {format_pipeline_report(result.pipeline)}"
    if result.status == "PASS":
        return (
            f"Anti-spam/templated: PASS — nearest {neighbor} (sim {result.similarity}) "
            f"— diffs: {diffs} — risk {result.templated_risk}{pipeline_bit}"
        )
    if result.status == "WARN":
        warn = "; ".join(result.warnings[:2])
        return (
            f"Anti-spam/templated: WARN — nearest {neighbor} (sim {result.similarity}) "
            f"— {warn} — risk {result.templated_risk}{pipeline_bit}"
        )
    block = "; ".join(result.blockers[:3])
    classes_bit = ""
    if result.unacceptable_classes:
        classes_bit = f" — classes: {','.join(result.unacceptable_classes)}"
    return (
        f"Anti-spam/templated: FAIL — nearest {neighbor} (sim {result.similarity}) "
        f"— {block} — risk {result.templated_risk}{classes_bit}{pipeline_bit} "
        f"— fix: .cursor/rules/engines/ENGINE_2_anti_spam.mdc (When FAIL → fix)"
    )


def build_all_fingerprints() -> dict[str, Fingerprint]:
    fps: dict[str, Fingerprint] = {}
    for task_dir in list_task_dirs(REPO_ROOT / "tasks") + list_pending_dirs():
        fp = fingerprint_task(task_dir)
        if fp:
            fps[fp.slug] = fp
    return fps


def resolve_task_dir(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def write_report(lines: list[str]) -> None:
    """Persist last pack-gate output for agents (jobs-local/ is gitignored)."""
    out_dir = REPO_ROOT / "jobs-local"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "anti-spam-last.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        pass


def run_pack_gate(
    slug: str,
    all_fps: dict[str, Fingerprint],
    platform: set[str],
    *,
    strict: bool = False,
    strict_repo: bool = False,
    all_meta: dict | None = None,
    rebuild_index: bool = False,
    use_llm: bool = False,
    include_pipeline: bool = False,
) -> tuple[int, list[str]]:
    """All anti-spam checks for pack_zip.sh — one call, no manual steps."""
    lines: list[str] = []
    code = 0

    zip_only = zip_only_spam(REPO_ROOT / "tasksubmit")
    if zip_only:
        preview = ", ".join(zip_only[:5])
        if len(zip_only) > 5:
            preview += f" (+{len(zip_only) - 5} more)"
        lines.append(f"repo: WARN zip-only in tasksubmit/ ({len(zip_only)}): {preview}")
        if strict_repo:
            code = 1

    clusters = same_day_zip_clusters(REPO_ROOT / "tasksubmit")
    if clusters:
        day, count, _names = clusters[-1]
        lines.append(
            f"repo: INFO largest same-day zip batch {day} ({count} zips) — avoid bulk upload"
        )

    result = check_one(
        slug,
        all_fps,
        platform,
        strict=strict,
        all_meta=all_meta,
        rebuild_index=rebuild_index,
        use_llm=use_llm,
    )
    lines.append(format_line(result, include_pipeline=include_pipeline))
    if include_pipeline and result.pipeline is not None:
        lines.append(f"  pipeline: {format_pipeline_report(result.pipeline)}")
    if result.status == "FAIL":
        code = 1
        for b in result.blockers:
            lines.append(f"  blocker: {b}")
    elif result.warnings:
        for w in result.warnings:
            lines.append(f"  warn: {w}")

    if platform:
        others = [
            check_one(
                s,
                all_fps,
                platform,
                strict=strict,
                all_meta=all_meta,
                rebuild_index=rebuild_index,
                use_llm=use_llm,
            )
            for s in sorted(all_fps)
            if s not in platform and s != slug
        ]
        o_fail = sum(1 for r in others if r.status == "FAIL")
        o_warn = sum(1 for r in others if r.status == "WARN")
        o_pass = len(others) - o_fail - o_warn
        if others:
            lines.append(
                f"repo: local-only not tracked ({len(others)}): "
                f"pass={o_pass} warn={o_warn} fail={o_fail} "
                f"(platform export + scripts/packed_for_upload.txt)"
            )

    return code, lines


def run_pack_summary(
    all_fps: dict[str, Fingerprint],
    platform: set[str],
    *,
    strict: bool = False,
    all_meta: dict | None = None,
) -> tuple[int, list[str]]:
    """End-of --all pack: compact not-submitted summary only."""
    if not platform:
        return 0, ["repo: SKIP not-submitted summary (no platform file)"]

    slugs = [s for s in sorted(all_fps) if s not in platform]
    results = [
        check_one(s, all_fps, platform, strict=strict, all_meta=all_meta)
        for s in slugs
    ]
    fail = sum(1 for r in results if r.status == "FAIL")
    warn = sum(1 for r in results if r.status == "WARN")
    lines = [
        f"repo: not-submitted summary — pass={len(results) - fail - warn} "
        f"warn={warn} fail={fail} (of {len(results)} local-only)"
    ]
    for r in results:
        if r.status == "FAIL":
            lines.append(f"  FAIL {r.slug}: {r.blockers[0] if r.blockers else 'unknown'}")
    return (1 if fail else 0), lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=str, help="Single task folder (tasks/<name>)")
    parser.add_argument("--task-name", type=str, help="Task slug under tasks/")
    parser.add_argument("--check", action="store_true", help="Exit 1 on FAIL (for pack_zip.sh)")
    parser.add_argument("--quiet", action="store_true", help="Only print on FAIL/WARN unless --verbose")
    parser.add_argument("--verbose", action="store_true", help="Print full JSON details")
    parser.add_argument(
        "--platform-file",
        type=str,
        default=str(DEFAULT_PLATFORM_FILE),
        help="Platform submission slugs (one per line); empty path to skip",
    )
    parser.add_argument("--all-local", action="store_true", help="Report all tasks under tasks/")
    parser.add_argument(
        "--not-submitted",
        action="store_true",
        help="With --all-local: only tasks absent from platform file",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as blockers")
    parser.add_argument("--list-spam-zips", action="store_true", help="List zip-only tasksubmit zips")
    parser.add_argument("--list-clusters", action="store_true", help="List same-day zip batches (5+)")
    parser.add_argument(
        "--pack-gate",
        action="store_true",
        help="All checks for pack_zip.sh (task + repo scan + not-submitted counts)",
    )
    parser.add_argument(
        "--pack-summary",
        action="store_true",
        help="After pack --all: compact not-submitted FAIL summary",
    )
    parser.add_argument(
        "--strict-repo",
        action="store_true",
        help="With --pack-gate: fail if any zip-only exists in tasksubmit/",
    )
    parser.add_argument(
        "--register-pack",
        action="store_true",
        help="After pack_zip success: add slug to scripts/packed_for_upload.txt",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Run multi-signal extract/embed/judge pipeline (see anti_spam_pipeline.py)",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rebuild jobs-local/anti-spam-index.json embedding index",
    )
    parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="Optional LLM judge when ANTI_SPAM_LLM=1 and OPENAI_API_KEY set",
    )
    args = parser.parse_args()

    platform_path = Path(args.platform_file) if args.platform_file else None
    platform = load_all_submission_slugs(platform_path)

    slug_early: str | None = args.task_name
    if args.task_dir:
        slug_early = resolve_task_dir(args.task_dir).name

    if args.register_pack:
        if not slug_early:
            parser.error("--register-pack requires --task-name or --task-dir")
        added, msg = register_packed_slug(slug_early)
        if not args.quiet or added:
            print(msg)
        return 0

    if args.list_spam_zips:
        bad = zip_only_spam(REPO_ROOT / "tasksubmit")
        if args.json:
            print(json.dumps({"zip_only": bad}, indent=2))
        else:
            for s in bad:
                print(s)
        return 1 if bad else 0

    if args.list_clusters:
        clusters = same_day_zip_clusters(REPO_ROOT / "tasksubmit")
        if args.json:
            print(json.dumps([{"day": d, "count": c, "tasks": n} for d, c, n in clusters], indent=2))
        else:
            for day, count, names in clusters:
                tail = "…" if len(names) > 8 else ""
                print(f"{day}: {count} zips — {', '.join(names[:8])}{tail}")
        return 0

    all_fps = build_all_fingerprints()
    all_meta = build_all_metadata(rebuild_index=args.rebuild_index)
    if args.rebuild_index and not args.pack_gate and not args.task_name and not args.task_dir and not args.all_local:
        print(f"OK rebuilt index: {REPO_ROOT / 'jobs-local' / 'anti-spam-index.json'} ({len(all_meta)} tasks)")
        return 0

    if args.pack_summary:
        code, lines = run_pack_summary(all_fps, platform, strict=args.strict, all_meta=all_meta)
        write_report(lines)
        if args.json:
            print(json.dumps({"lines": lines, "exit_code": code}, indent=2))
        else:
            for line in lines:
                print(line)
        return code

    if args.pack_gate:
        if not slug_early:
            parser.error("--pack-gate requires --task-name or --task-dir")
        if all_meta is None:
            all_meta = build_all_metadata(rebuild_index=args.rebuild_index)
        code, lines = run_pack_gate(
            slug_early,
            all_fps,
            platform,
            strict=args.strict,
            strict_repo=args.strict_repo,
            all_meta=all_meta,
            rebuild_index=args.rebuild_index,
            use_llm=args.llm_judge,
            include_pipeline=True,
        )
        write_report(lines)
        if args.json:
            print(json.dumps({"lines": lines, "exit_code": code, "slug": slug_early}, indent=2))
        else:
            for line in lines:
                print(line)
            if code:
                for line in lines:
                    if line.startswith("  blocker:"):
                        print(line, file=sys.stderr)
        return code

    if args.all_local:
        slugs = sorted(all_fps.keys())
        if args.not_submitted and platform:
            slugs = [s for s in slugs if s not in platform]
        results = [
            check_one(
                s,
                all_fps,
                platform,
                strict=args.strict,
                all_meta=all_meta,
                rebuild_index=args.rebuild_index,
                use_llm=args.llm_judge,
            )
            for s in slugs
        ]
        fail = sum(1 for r in results if r.status == "FAIL")
        warn = sum(1 for r in results if r.status == "WARN")
        if args.json:
            print(json.dumps([asdict(r) for r in results], indent=2))
        else:
            for r in results:
                if args.not_submitted and r.on_platform:
                    continue
                plat = "on-platform" if r.on_platform else "local-only"
                print(f"{r.slug} [{plat}] {format_line(r, include_pipeline=args.pipeline)}")
            print(f"--- summary: pass={len(results) - fail - warn} warn={warn} fail={fail} ---")
        return 1 if fail else 0

    slug: str | None = args.task_name
    if args.task_dir:
        slug = resolve_task_dir(args.task_dir).name
    if not slug:
        parser.error("one of --task-dir, --task-name, or --all-local is required")

    if SPAM_SLUG_RE.search(slug):
        print(f"ERROR: spam slug pattern: {slug}", file=sys.stderr)
        return 1

    task_dir = locate_task_dir(slug)
    if task_dir is None:
        zip_path = REPO_ROOT / "tasksubmit" / f"{slug}.zip"
        if zip_path.is_file():
            print(
                f"ERROR: zip-only spam — {zip_path} exists but tasks/{slug}/ missing",
                file=sys.stderr,
            )
            return 1
        print(
            f"ERROR: pending/{slug}/ or tasks/{slug}/ not found",
            file=sys.stderr,
        )
        return 1

    result = check_one(
        slug,
        all_fps,
        platform,
        strict=args.strict,
        all_meta=all_meta,
        rebuild_index=args.rebuild_index,
        use_llm=args.llm_judge,
    )

    if args.json or args.verbose:
        payload = asdict(result)
        if result.pipeline is not None:
            payload["pipeline_detail"] = pipeline_to_dict(result.pipeline)
        print(json.dumps(payload, indent=2))
    elif not args.quiet or result.status != "PASS":
        print(format_line(result, include_pipeline=args.pipeline or args.verbose))

    if result.blockers and not args.json:
        for b in result.blockers:
            print(f"  blocker: {b}", file=sys.stderr)
    if result.warnings and (args.verbose or result.status == "WARN"):
        for w in result.warnings:
            print(f"  warn: {w}", file=sys.stderr)

    if args.check or args.task_dir or args.task_name:
        return 1 if result.status == "FAIL" else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
