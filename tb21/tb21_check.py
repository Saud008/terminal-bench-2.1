#!/usr/bin/env python3
"""Local static gate for Caudal Terminal Bench 2.1 task bundles.

Mirrors the blocking CI checks (validate_task_fields, check_task_absolute_path,
pinned_dependencies, check_pinned_images, check_sanctioned_base_images,
check_build_context_size, tests_or_solution_in_image, check_dockerfile_references,
check_test_sh, check_privileged_containers, ruff), the warning-level Dockerfile
checks, the rubric.txt format rules, the TB 2.1 diversity gates, the pool's
Master Ship Checklist rules for sections A-F (schema_version 1.1, 7200 timeouts,
allow_internet = true, delivery layout) and a personal-path / stb scrub. It does
not replace harbor, LLMaJ, run_k.sh or tb21_ship_check.py.

Expected layout: <slug>/<slug>/{instruction.md,task.toml,environment,solution,tests}
with <slug>/rubric.txt beside the inner directory.

Usage:
    py -3 tb21/tb21_check.py <slug-dir> [<slug-dir> ...]   (outer or inner path)

Exit code is 1 when any ERROR is reported.
"""

from __future__ import annotations

import ast
import getpass
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

CATEGORIES = {
    "system-administration",
    "build-and-dependency-management",
    "data-processing",
    "games",
    "software-engineering",
    "machine-learning",
    "debugging",
    "security",
    "scientific-computing",
}
DIFFICULTIES = {"easy", "medium", "hard", "unknown"}
CANONICAL_IMAGES = {
    "public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb",
    "public.ecr.aws/docker/library/node:22-bookworm-slim@sha256:f3a68cf41a855d227d1b0ab832bed9749469ef38cf4f58182fb8c893bc462383",
    "public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac",
    "public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36",
    "public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14",
    "public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c",
    "public.ecr.aws/docker/library/ruby:3.3-slim-bookworm@sha256:e76733e94b3a5893e4a141024ef3a583dc10781dc24becebf74f9c9f9a33e3df",
    "public.ecr.aws/docker/library/maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e",
    "public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d",
    "public.ecr.aws/docker/library/ubuntu:24.04@sha256:0d39fcc8335d6d74d5502f6df2d30119ff4790ebbb60b364818d5112d9e3e932",
}
REQUIRED_FILES = [
    "instruction.md",
    "task.toml",
    "solution/solve.sh",
    "tests/test.sh",
    "tests/test_outputs.py",
]
INNER_ALLOWED = {"instruction.md", "task.toml", "environment", "solution", "tests"}
PACKAGING_JUNK = {
    ".DS_Store",
    "__MACOSX",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".git",
    "Thumbs.db",
    "SOURCE.txt",
}
TIMEOUT = 7200
AI_SCAFFOLDING = {"claude.md", "agents.md", "skills.md", ".cursor", ".claude", ".cursorrules"}
CODEBASE_EXCLUDE = {"Dockerfile", "docker-compose.yaml", "docker-compose.yml", ".dockerignore"}
MIB = 1024 * 1024


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warns: list[str] = []

    def err(self, code: str, msg: str) -> None:
        self.errors.append(f"ERROR [{code}] {msg}")

    def warn(self, code: str, msg: str) -> None:
        self.warns.append(f"WARN  [{code}] {msg}")


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > 2 * MIB:
            return None
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def rel(task: Path, path: Path) -> str:
    return path.relative_to(task).as_posix()


def all_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file())


def is_junk(path: Path) -> bool:
    return path.name in PACKAGING_JUNK or path.name.startswith("._") or path.suffix == ".pyc"


def resolve_layout(arg: str) -> tuple[Path | None, Path]:
    """Return (outer, inner) for either the outer <slug>/ or the inner <slug>/<slug>/ path."""
    p = Path(arg).resolve()
    if (p / p.name).is_dir():
        return p, p / p.name
    if p.parent.name == p.name:
        return p.parent, p
    return None, p


# --------------------------------------------------------------------------- structure


def check_structure(task: Path, outer: Path | None, r: Report) -> None:
    if outer is None:
        r.err("layout", f"task must live at <slug>/<slug>/ with rubric.txt in <slug>/ (got {task})")
    elif not (outer / "rubric.txt").is_file():
        r.err("structure", f"missing {outer.name}/rubric.txt (beside the inner task directory)")
    for name in REQUIRED_FILES:
        if not (task / name).is_file():
            r.err("structure", f"missing required file {name}")
    env = task / "environment"
    if not (env / "Dockerfile").is_file() and not (env / "docker-compose.yaml").is_file():
        r.err("structure", "missing environment/Dockerfile (or environment/docker-compose.yaml)")

    for child in task.iterdir():
        if is_junk(child):
            continue
        if child.name not in INNER_ALLOWED:
            r.err("delivery", f"inner task dir may only hold {sorted(INNER_ALLOWED)} — remove/move '{child.name}'")

    for path in task.rglob("*"):
        if is_junk(path):
            r.err("delivery", f"packaging artifact must be removed: {rel(task, path)}")
        if path.name.lower() in AI_SCAFFOLDING:
            r.err("ai-scaffolding", f"AI-framework filename not allowed: {rel(task, path)}")

    for path in all_files(task):
        head = path.read_bytes()[:3] if path.is_file() else b""
        if head == b"\xef\xbb\xbf":
            r.err("encoding", f"{rel(task, path)} starts with a UTF-8 BOM (Windows editor/PowerShell) — save as UTF-8 without BOM")
        if path.suffix in {".sh", ".py", ".toml"} or path.name == "Dockerfile":
            if b"\r\n" in path.read_bytes():
                r.err("encoding", f"{rel(task, path)} has CRLF line endings — convert to LF (breaks bash/shebangs in Linux)")
        text = read_text(path)
        if text and "<<REPLACE" in text:
            r.err("placeholder", f"skeleton placeholder left in {rel(task, path)}")

    slug = task.name
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)+", slug):
        r.warn("name", f"task folder '{slug}' should be descriptive kebab-case")
    if slug in {"task1", "my-task", "test"} or re.search(
        r"(^|-)(hardened|fixed|patched|final|draft|v\d+|round\d*|copy|tmp|wip)(-|$)", slug
    ):
        r.err("name", f"task name '{slug}' is generic or reveals process history")


# --------------------------------------------------------------------------- task.toml


def count_codebase(env: Path) -> int:
    if not env.is_dir():
        return 0
    return sum(
        1
        for p in all_files(env)
        if p.name not in CODEBASE_EXCLUDE and not is_junk(p) and not (set(p.parts) & PACKAGING_JUNK)
    )


def check_toml(task: Path, r: Report) -> dict:
    path = task / "task.toml"
    if not path.is_file():
        return {}
    raw = path.read_text(encoding="utf-8")
    first = raw.lstrip("\ufeff").splitlines()[0].strip() if raw.strip() else ""
    if first != 'schema_version = "1.1"':
        r.err("toml", 'first line must be exactly: schema_version = "1.1" (ship check 46)')
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        r.err("toml", f"task.toml does not parse: {exc}")
        return {}

    for key in data:
        if key == "version":
            r.err("toml", "'version' is the old 2.0 schema key — the pool uses schema_version = \"1.1\"")
        elif key not in {"schema_version", "task", "metadata", "verifier", "agent", "environment", "solution"}:
            r.warn("toml", f"unexpected top-level key/table '{key}'")
    if re.search(r"reference_pattern", raw):
        r.err("toml", "[reference_pattern] / pipeline metadata must not ship (ship check 49)")

    task_tbl = data.get("task", {})
    desc = task_tbl.get("description")
    if not isinstance(desc, str) or len(desc.split()) < 4:
        r.err("toml", "[task].description must be an accurate one-line description (ship check 47)")
    keywords = task_tbl.get("keywords")
    if not isinstance(keywords, list) or not keywords:
        r.err("toml", "[task].keywords must be a non-empty list (ship check 47)")
    authors = task_tbl.get("authors")
    if not isinstance(authors, list) or not authors or not all(
        isinstance(a, dict) and a.get("name") and a.get("email") for a in authors
    ):
        r.err("toml", "[[task.authors]] with name and email is required (ship check 47)")

    meta = data.get("metadata", {})
    tables = [data] + [v for v in data.values() if isinstance(v, dict)]
    for key in ("id", "task_id", "task-id"):
        if any(key in t for t in tables):
            r.err("toml", f"'{key}' was removed in TB 2.1 — delete it")
    for key in ("author_name", "author_email"):
        if key not in meta:
            r.warn("toml", f"[metadata].{key} missing (public guide field; 'anonymous' is fine)")
    required = [
        "difficulty",
        "category",
        "codebase_size",
        "languages",
        "tags",
        "expert_time_estimate_min",
        "junior_time_estimate_min",
    ]
    for key in required:
        if key not in meta:
            r.err("toml", f"[metadata].{key} is required")

    category = meta.get("category")
    if category is not None and category not in CATEGORIES:
        r.err("toml", f"category '{category}' is not one of the 9 TB 2.1 categories")

    difficulty = meta.get("difficulty")
    if difficulty is not None and difficulty not in DIFFICULTIES:
        r.err("toml", f"difficulty '{difficulty}' must be easy|medium|hard|unknown")
    if difficulty == "easy":
        r.err("diversity", "easy model difficulty is blocked in TB 2.1 (only medium/hard accepted)")
    if difficulty == "unknown":
        r.warn("toml", "difficulty is 'unknown' — set it from the run_k.sh k=5 result before submitting")

    size = meta.get("codebase_size")
    if size is not None and size not in {"minimal", "small", "large"}:
        r.err("toml", f"codebase_size '{size}' must be minimal|small|large (lowercase)")
    if size == "minimal":
        r.err("diversity", "codebase_size 'minimal' is blocked in TB 2.1 (use small 20+ or large 200+)")
    n = count_codebase(task / "environment")
    actual = "minimal" if n < 20 else ("small" if n < 200 else "large")
    if n < 20:
        r.err("diversity", f"environment/ has only {n} files (excl. Dockerfile/compose) — need 20+ real files")
    elif size in {"small", "large"} and size != actual:
        r.warn("codebase-size", f"declared '{size}' but environment/ has {n} files (≈ '{actual}')")

    languages = meta.get("languages")
    if languages is not None:
        if not isinstance(languages, list) or not languages:
            r.err("toml", "languages must be a non-empty list")
        else:
            lowered = [str(x).lower() for x in languages]
            if "python" in lowered:
                if difficulty not in {"hard", "unknown"}:
                    r.err("diversity", "Python tasks must be hard model difficulty")
                if len(lowered) > 1:
                    r.warn("toml", "list python only if it is the primary language (pytest tests don't count)")

    tags = meta.get("tags")
    if tags is not None and (not isinstance(tags, list) or not 3 <= len(tags) <= 6):
        r.err("toml", "tags must be a list of 3-6 keywords")

    expert, junior = meta.get("expert_time_estimate_min"), meta.get("junior_time_estimate_min")
    if isinstance(expert, (int, float)) and isinstance(junior, (int, float)) and junior < expert:
        r.warn("toml", "junior_time_estimate_min is lower than expert_time_estimate_min")

    env = data.get("environment", {})
    timeouts = {
        "[verifier].timeout_sec": data.get("verifier", {}).get("timeout_sec"),
        "[agent].timeout_sec": data.get("agent", {}).get("timeout_sec"),
        "[environment].build_timeout_sec": env.get("build_timeout_sec"),
    }
    for name, value in timeouts.items():
        if value != TIMEOUT:
            r.err("toml", f"{name} is {value}; pool convention is {TIMEOUT} (ship check 48)")

    for key in ("cpus", "memory_mb", "storage_mb", "allow_internet"):
        if key not in env:
            r.err("toml", f"[environment].{key} is required")
    if env.get("allow_internet") is not True:
        r.err("toml", "[environment].allow_internet must be true (ship check 50)")

    compose = task / "environment" / "docker-compose.yaml"
    if not compose.is_file():
        compose = task / "environment" / "docker-compose.yml"
    if compose.is_file():
        if meta.get("custom_docker_compose") is not True:
            r.err("toml", "docker-compose present: set custom_docker_compose = true in [metadata]")
        text = compose.read_text(encoding="utf-8")
        services = re.search(r"^services:\s*\n((?:[ \t]+.*\n?|\s*\n)*)", text, re.M)
        count = len(re.findall(r"^[ ]{2}[A-Za-z0-9_.-]+:\s*$", services.group(1), re.M)) if services else 0
        if count > 1 and meta.get("is_multi_container") is not True:
            r.err("toml", f"compose defines {count} services: set is_multi_container = true in [metadata]")

    if re.search(r"[A-Za-z]:\\|/Users/|/private/tmp/|/home/", raw):
        r.err("scrub", "task.toml contains a local machine path")
    return data


# --------------------------------------------------------------------------- instruction.md


def check_instruction(task: Path, r: Report) -> None:
    path = task / "instruction.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    low = text.lower()

    if "canary" in low or "benchmark data should never" in low:
        r.err("instruction", "canary string found (old skeleton) — remove it")
    slug = task.name.lower()
    if slug in low or slug.replace("-", " ") in low:
        r.warn("instruction", "task name appears in instruction.md")
    if re.search(r"\b(grader|graded by|pytest|test_outputs|the test suite|the verifier)\b|/tests\b|/opt/verifier", low):
        r.err("instruction", "mentions grading tooling (grader/test suite/the verifier/pytest//tests//opt/verifier)")
    if re.search(r"\bhidden tests?\b|\btest suite\b", low):
        r.warn("instruction", "mentions tests — keep framing inside the task fiction")
    if re.search(r"\boffline\b|\bno (internet|network)\b|without (internet|network)|(don't|do not|never) (use|access|reach) the (internet|network)", low):
        r.err("instruction", "tells the agent to stay offline — tasks run with allow_internet = true (ship check 50)")
    approx_tokens = len(re.findall(r"\w+|[^\w\s]", text))
    if approx_tokens >= 1500:
        r.err("instruction", f"~{approx_tokens} tokens — must stay under 1500 (ship check 0)")
    outside_ticks = re.sub(r"`[^`\n]*`", " ", text)
    bare = sorted(set(re.findall(r"(?<![\w`/.:-])(/(?:app|data|opt|etc|var|srv|usr|home|tmp|root|workspace|logs|output|mnt|repo|src)(?:/[\w.@+-]+)*/?)", outside_ticks)))
    for p in bare[:10]:
        r.err("absolute-path", f"absolute path {p} must be written in backticks (ship check 0)")
    if re.search(r"you are an? (expert|senior|experienced)|your (goal|task) is to|i hope this helps", low):
        r.warn("instruction", "reads LLM-generated ('You are an expert…' / 'Your goal is to…')")
    if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", text):
        r.err("instruction", "emoji found")

    words = len(re.findall(r"\S+", text))
    if words > 300:
        r.warn("instruction", f"{words} words — TB 2.1 wants concise prompts (~150-200 words, max 3 paragraphs)")
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    if len(paragraphs) > 5:
        r.warn("instruction", f"{len(paragraphs)} paragraphs/blocks — keep to about three")
    headings = len(re.findall(r"^\s{0,3}#{1,6}\s", text, re.M))
    bullets = len(re.findall(r"^\s*(?:[-*+]|\d+[.)])\s", text, re.M))
    bold = len(re.findall(r"\*\*[^*]+\*\*|__[^_]+__", text))
    if headings:
        r.warn("instruction", f"{headings} markdown heading(s) — reads like documentation, not a prompt")
    if bullets > 20:
        r.err("instruction", f"{bullets} bullets — QC cap is 20")
    elif bullets > 8:
        r.warn("instruction", f"{bullets} bullets — heavy structure")
    if bold >= 3:
        r.warn("instruction", f"{bold} bold markers — bold solution details read as hints")
    if re.search(r"(?i)\b(step \d|first,? (run|use|open)|hint|look for)\b", text):
        r.warn("instruction", "possible step-by-step / hint language")

    tokens = text.replace("`", " ").split()
    flagged: set[str] = set()
    for tok in tokens:
        t = tok.strip("`\"'(),;:!?[]{}<>*")
        t = t.rstrip(".")
        if not t or "://" in t or t.startswith("/") or t in flagged:
            continue
        if t.startswith("~/"):
            flagged.add(t)
            r.err("absolute-path", f"home-relative path '{t}' — use an absolute path")
        elif "/" in t and (
            t.startswith(("./", "../")) or re.search(r"\.[A-Za-z0-9]{1,6}$", t.split("/")[-1])
        ):
            flagged.add(t)
            r.err("absolute-path", f"relative path '{t}' — use an absolute path like /app/{t.lstrip('./')}")


# --------------------------------------------------------------------------- Dockerfile / environment


def dockerfile_instructions(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    buf = ""
    for line in text.splitlines():
        stripped = line.strip()
        if not buf and (not stripped or stripped.startswith("#")):
            continue
        if stripped.startswith("#"):
            continue
        if stripped.endswith("\\"):
            buf += stripped[:-1] + " "
            continue
        buf += stripped
        parts = buf.split(None, 1)
        out.append((parts[0].upper(), parts[1] if len(parts) > 1 else ""))
        buf = ""
    if buf.strip():
        parts = buf.split(None, 1)
        out.append((parts[0].upper(), parts[1] if len(parts) > 1 else ""))
    return out


def image_repo(image: str) -> str:
    name = image.split("@")[0]
    last = name.split("/")[-1]
    if ":" in last:
        name = name.rsplit(":", 1)[0]
    return name


def check_image_pin(image: str, where: str, r: Report) -> None:
    if image == "scratch":
        return
    if "$" in image:
        r.warn("pinned-images", f"{where}: image '{image}' uses a build arg — cannot verify pin")
        return
    if "@sha256:" in image:
        return
    last = image.split("/")[-1]
    tag = last.split(":", 1)[1] if ":" in last else None
    if tag is None or tag == "latest":
        r.err("pinned-images", f"{where}: image '{image}' is unpinned or uses latest")
    else:
        r.warn("pinned-images", f"{where}: '{image}' is tag-pinned; prefer the canonical digest reference")


def split_commands(run: str) -> list[str]:
    return [c.strip() for c in re.split(r"&&|\|\||;|\|", run) if c.strip()]


def check_pip(cmd: str, env: Path, where: str, r: Report) -> None:
    m = re.search(r"\bpip3?\s+install\b(.*)", cmd)
    if not m:
        return
    tokens = m.group(1).split()
    skip_next = False
    for i, tok in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if tok in {"-r", "--requirement", "-c", "--constraint"} and i + 1 < len(tokens):
            skip_next = True
            req = env / Path(tokens[i + 1]).name
            matches = [req] if req.is_file() else list(env.rglob(Path(tokens[i + 1]).name))
            for req_file in matches[:1]:
                check_requirements(req_file, env, r)
            continue
        if tok in {"-f", "--find-links", "-i", "--index-url", "--extra-index-url", "-t", "--target", "--prefix"}:
            skip_next = True
            continue
        if tok.startswith("-") or tok.endswith(".whl") or tok.startswith(("/", ".")) or "://" in tok:
            continue
        if "==" not in tok:
            r.err("pinned-deps", f"{where}: pip package '{tok}' is not pinned with ==")


def check_requirements(path: Path, env: Path, r: Report) -> None:
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.split("#", 1)[0].strip()
        if not s or s.startswith(("-", "--")):
            continue
        if "==" not in s:
            r.err("pinned-deps", f"{path.relative_to(env.parent).as_posix()}:{n} '{s}' is not pinned with ==")


def check_dockerfile(task: Path, r: Report) -> None:
    env = task / "environment"
    dockerfiles = sorted(env.glob("Dockerfile*")) if env.is_dir() else []
    for df in dockerfiles:
        where = rel(task, df)
        text = df.read_text(encoding="utf-8")
        instrs = dockerfile_instructions(text)
        stages: dict[str, str] = {}
        final_base = None
        for op, args in instrs:
            if op != "FROM":
                continue
            toks = [t for t in args.split() if not t.startswith("--")]
            if not toks:
                continue
            image = toks[0]
            alias = toks[2] if len(toks) >= 3 and toks[1].upper() == "AS" else None
            base = stages.get(image, image)
            if image not in stages:
                check_image_pin(image, where, r)
            if alias:
                stages[alias] = base
            final_base = base

        if final_base and final_base != "scratch":
            if final_base in CANONICAL_IMAGES:
                pass
            elif image_repo(final_base) in {image_repo(c) for c in CANONICAL_IMAGES}:
                r.warn("sanctioned-base", f"{where}: canonical family but not the canonical digest: {final_base}")
            elif "@sha256:" in final_base and re.match(r"(python:|mcr\.microsoft\.com/|ghcr\.io/)", final_base):
                r.warn("sanctioned-base", f"{where}: sanctioned but non-canonical final base — prefer the canonical ECR ref")
            else:
                justified = re.search(r"#.*(justif|canonical|non-canonical|base image)", text, re.I)
                readme = task / "README.md"
                if not justified and readme.is_file() and "base image" in readme.read_text(encoding="utf-8").lower():
                    justified = True
                if justified:
                    r.warn("sanctioned-base", f"{where}: non-canonical final base {final_base} — reviewer will judge the justification")
                else:
                    r.err("sanctioned-base", f"{where}: non-canonical final base {final_base} with no justification comment")

        runs = [args for op, args in instrs if op == "RUN"]
        all_run = "\n".join(runs)
        if not re.search(r"\btmux\b", all_run) or not re.search(r"\basciinema\b", all_run):
            r.err("runtime", f"{where}: tmux and asciinema must be installed (agent runs fail without them)")
        if not any(op == "WORKDIR" for op, _ in instrs):
            r.warn("workdir", f"{where}: no WORKDIR set (test.sh refuses to run from /)")

        apt_updates = 0
        for run in runs:
            if re.search(r"apt-get\s+(upgrade|dist-upgrade)", run):
                r.warn("apt", f"{where}: never run apt-get upgrade")
            if re.search(r"apt-get\s+update", run):
                apt_updates += 1
            if re.search(r"apt-get\s+install", run):
                if "--no-install-recommends" not in run:
                    r.warn("apt", f"{where}: apt-get install without --no-install-recommends")
                if "/var/lib/apt/lists" not in run:
                    r.warn("apt", f"{where}: apt lists not removed in the same RUN")
            if re.search(r"(curl|wget)[^|]*\|\s*(ba|z)?sh", run):
                r.warn("reproducible", f"{where}: curl|sh — pin version and verify sha256")
            elif re.search(r"\b(curl|wget)\b.*https?://", run):
                r.warn("web-fetch", f"{where}: downloads from the web at build time — only packages allowed; vendor data into environment/")
            if re.search(r"git\s+clone", run) and "checkout" not in run:
                r.warn("reproducible", f"{where}: git clone without pinning a commit")
            if re.search(r"<<-?\s*['\"]?[A-Z_]+", run):
                r.warn("heredoc", f"{where}: heredoc in RUN — ship files and COPY them")
            if re.search(r"\b(chmod|chown)\s+-R\b", run):
                r.warn("permissions", f"{where}: recursive chmod/chown — use COPY --chmod/--chown")
            if re.search(r"(mkdir|chown|chmod|rm)[^&;]*\s/(tests|solution|oracle)\b", run):
                r.err("reserved-dirs", f"{where}: must not create/modify /tests, /solution or /oracle")
            for cmd in split_commands(run):
                check_pip(cmd, env, where, r)
                m = re.search(r"\bnpm\s+(install|i)\b(.*)", cmd)
                if m:
                    pkgs = [t for t in m.group(2).split() if not t.startswith("-")]
                    if not pkgs:
                        r.warn("pinned-deps", f"{where}: prefer 'npm ci' with package-lock.json over 'npm install'")
                    for p in pkgs:
                        if p.count("@") < (2 if p.startswith("@") else 1):
                            r.err("pinned-deps", f"{where}: npm package '{p}' is not version-pinned")
                if re.search(r"\bgo\s+install\s+\S+@latest", cmd):
                    r.err("pinned-deps", f"{where}: go install @latest is unpinned")
                if re.search(r"\bcargo\s+install\b", cmd) and "--version" not in cmd and "--locked" not in cmd:
                    r.warn("pinned-deps", f"{where}: cargo install without --version/--locked")
                if re.search(r"\bgem\s+install\b", cmd) and not re.search(r"\s(-v|--version)\s", cmd):
                    r.warn("pinned-deps", f"{where}: gem install without -v")
        if apt_updates > 1:
            r.warn("apt", f"{where}: {apt_updates} separate apt-get update transactions — consolidate")

        for op, args in instrs:
            if op in {"COPY", "ADD"}:
                srcs = [t for t in args.split() if not t.startswith("--")][:-1]
                for s in srcs:
                    norm = s.strip("\"'[],").lstrip("./")
                    if re.match(r"(tests|solution)(/|$)", norm) or "/tests" in s or "/solution" in s:
                        r.err("tests-in-image", f"{where}: {op} {args} copies tests/solution into the image")
                    if s in {".", "./"}:
                        r.warn("layers", f"{where}: '{op} . ' copies the whole context — prefer narrow COPY")
        if re.search(r"solve\.sh|test_outputs\.py|tests/test\.sh", text):
            r.err("dockerfile-references", f"{where}: references solution/test files")

    for compose in [env / "docker-compose.yaml", env / "docker-compose.yml"]:
        if not compose.is_file():
            continue
        where = rel(task, compose)
        text = compose.read_text(encoding="utf-8")
        if re.search(r"privileged:\s*true", text) or re.search(r"SYS_ADMIN|NET_ADMIN|SYS_MODULE|docker\.sock", text):
            r.err("privileged", f"{where}: privileged mode / dangerous capability / docker.sock")
        if re.search(r"context:\s*\.\.", text):
            r.err("context", f"{where}: build context outside environment/")
        if re.search(r":\s*/(logs/verifier|logs/artifacts|tests|solution)\b", text):
            r.err("reserved-mounts", f"{where}: mounts a reserved path")
        for image in re.findall(r"^\s*image:\s*['\"]?([^\s'\"]+)", text, re.M):
            check_image_pin(image, where, r)

    if not env.is_dir():
        return
    files = all_files(env)
    total = sum(p.stat().st_size for p in files)
    if total > 100 * MIB:
        r.err("context-size", f"environment/ is {total / MIB:.1f} MiB (max 100)")
    for p in files:
        if p.stat().st_size > 50 * MIB:
            r.err("context-size", f"{rel(task, p)} is over 50 MiB")
    if not (env / ".dockerignore").is_file():
        r.warn("dockerignore", "environment/.dockerignore missing (template in tb21/skeleton)")
    for p in env.rglob("*"):
        if p.name in {".env", "node_modules"} or p.suffix == ".log":
            r.warn("hygiene", f"clutter/secret candidate in build context: {rel(task, p)}")

    tell = re.compile(
        r"FIXME|\bXXX\b|planted|deliberate|intentional(ly)?\s+(bug|broken|wrong)"
        r"|for the (grader|tests?|verifier)\b|the fix is|\bhint:",
        re.I,
    )
    scan = files + (all_files(task / "solution") if (task / "solution").is_dir() else [])
    hits = 0
    for p in scan:
        text = read_text(p)
        if not text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if tell.search(line) or re.search(r"\bBUG\b|\bTODO\b", line):
                hits += 1
                if hits <= 15:
                    r.warn("defect-tell", f"{rel(task, p)}:{n} grep hit (ship check 12 — remove or justify): {line.strip()[:100]}")
            if p in files and re.search(r"\b(decoy|red[- ]herring)\b", line, re.I):
                r.err("decoy-label", f"{rel(task, p)}:{n} labels a decoy as a decoy (ship check 23)")
    if hits > 15:
        r.warn("defect-tell", f"... {hits - 15} more grep hits")

    common = {"db", "io", "ui", "os", "go", "js", "ts", "v1", "v2", "v3", "api", "cmd", "pkg", "lib", "src", "bin",
              "etc", "app", "web", "net", "log", "tmp", "doc", "img", "css", "sql", "cli", "ci", "gc", "id", "ip", "rpc"}
    for p in env.rglob("*"):
        stem = p.stem.lower() if p.is_file() else p.name.lower()
        if stem not in common and re.fullmatch(r"[a-z]{1,3}\d{1,2}|[a-z]{1,2}", stem):
            r.warn("naming", f"{rel(task, p)}: opaque short name — must be decodable (ship check 15)")

    ref_exts = {".md", ".json", ".yaml", ".yml", ".toml", ".csv", ".txt", ".sh", ".conf", ".ini", ".sql", ".xml", ".cfg", ".tsv", ".env.example"}
    bundle_texts = {p: read_text(p) or "" for p in all_files(task) if not is_junk(p)}
    for p in files:
        if p.suffix.lower() not in ref_exts or p.name in {".dockerignore", "README.md", "go.sum", "package-lock.json"}:
            continue
        if not any(p.name in text for q, text in bundle_texts.items() if q != p):
            r.warn("unreferenced", f"{rel(task, p)} is referenced nowhere else in the bundle (ship check 17)")


# --------------------------------------------------------------------------- tests / solution


def check_test_sh(task: Path, r: Report) -> None:
    path = task / "tests" / "test.sh"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))
    if not text.startswith("#!"):
        r.warn("test-sh", "missing shebang")
    if "/logs/verifier/reward.txt" not in code and "/logs/verifier/reward.json" not in code:
        r.err("test-sh", "never writes /logs/verifier/reward.txt")
    if "mkdir -p /logs/verifier" not in code:
        r.warn("test-sh", "add 'mkdir -p /logs/verifier' before running pytest")
    if not re.search(r"\bpytest\b", code):
        r.err("test-sh", "does not run pytest (all verifiers must be Python pytest)")
    if re.search(r"^\s*set\s+-[a-zA-Z]*e", code, re.M) or "errexit" in code:
        r.err("test-sh", "set -e can exit before the reward is written — use 'set -uo pipefail'")
    if re.search(r"\buvx\b|\bnpm\s+(install|i|ci)\b|\bcurl\b|\bwget\b|git\s+clone|apt-get|apk\s+add|cargo\s+(fetch|install)|go\s+(get|install|mod\s+download)|mvn\s+dependency", code):
        r.err("test-sh", "installs/fetches at runtime — bake verifier deps into the image")
    for m in re.finditer(r"\bpip3?\s+install\b[^\n]*", code):
        if "--no-index" not in m.group(0):
            r.err("test-sh", "pip install at runtime (only '--no-index -f /opt/wheels' is allowed)")
    if re.search(r"\bgo\s+test\b|\bmvn\s+test\b|\bgradle\w*\s+test\b|\bnpm\s+test\b|\bjest\b|\bcargo\s+test\b", code):
        r.err("test-sh", "delegates to a non-pytest test framework")
    if "/oracle" in code or "EVAL_IS_ORACLE" in code:
        r.err("test-sh", "oracle-specific logic — oracle and agent must be verified identically")
    if re.search(r"\$TEST_DIR\b|\$\{TEST_DIR\}", code) and not re.search(r"TEST_DIR=\"?\$\{TEST_DIR:-", code):
        r.err("test-sh", "TEST_DIR used without a default (TEST_DIR=\"${TEST_DIR:-/tests}\")")
    lines = [ln.strip() for ln in code.splitlines() if ln.strip()]
    if lines and lines[-1].startswith("exit") and "fi" in lines[:-1]:
        r.err("test-sh", "trailing exit after the reward block fails check_test_sh — remove it")
    if lines and lines[-1] != "fi":
        r.warn("test-sh", "canonical test.sh ends with the reward if/else block")


def check_tests_py(task: Path, r: Report) -> None:
    tests_dir = task / "tests"
    if not tests_dir.is_dir():
        return
    total = 0
    for path in sorted(tests_dir.rglob("*.py")):
        where = rel(task, path)
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            r.err("tests", f"{where}: syntax error: {exc}")
            continue
        nodes: list[ast.AST] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                nodes.extend(node.body)
            else:
                nodes.append(node)
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                total += 1
                doc = ast.get_docstring(node)
                if not doc or len(doc.split()) < 3:
                    r.err("docstrings", f"{where}:{node.lineno} {node.name} needs an informative docstring")
        if re.search(r"time\.(time|perf_counter|monotonic)\(\)", src) and re.search(r"assert[^\n]*(elapsed|duration|latency|ms|seconds)", src, re.I):
            r.warn("latency", f"{where}: looks like a latency/performance assertion (not allowed)")
        for url in re.findall(r"https?://([^/\s\"']+)", src):
            if not re.match(r"(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])", url):
                r.warn("network", f"{where}: references external host {url} — tests must be offline")
        if re.search(r"/oracle\b|EVAL_IS_ORACLE", src):
            r.err("tests", f"{where}: oracle-specific branching")
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Add)
                and isinstance(node.left, ast.Constant)
                and isinstance(node.left.value, str)
                and isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, str)
            ):
                r.err("obfuscation", f"{where}:{node.lineno} string-literal concatenation (ship check 41)")
        all_test_src = "\n".join(p.read_text(encoding="utf-8") for p in tests_dir.rglob("*.py"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("test"):
                if len(re.findall(rf"\b{re.escape(node.name)}\b", all_test_src)) <= 1:
                    r.err("dead-code", f"{where}:{node.lineno} helper '{node.name}' is never used (ship check 42)")
    if total == 0:
        r.err("tests", "no pytest test functions found")
    elif total > 25:
        r.warn("tests", f"{total} tests — long suites are a review red flag; keep one per requirement")


def check_solve(task: Path, r: Report) -> None:
    path = task / "solution" / "solve.sh"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    code = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if not text.startswith("#!"):
        r.warn("solve", "missing shebang (#!/usr/bin/env bash)")
    if not re.search(r"set\s+-euo\s+pipefail", text):
        r.warn("solve", "add 'set -euo pipefail'")
    joined = "\n".join(code)
    if re.search(r"\b(curl|wget)\b[^\n]*https?://(?!localhost|127\.0\.0\.1)", joined) or re.search(
        r"\bpip3?\s+install\b(?![^\n]*--no-index)|\bapt-get\s+install|\bnpm\s+(install|i)\b|git\s+clone|go\s+get\b", joined
    ):
        r.err("solve", "oracle downloads/installs at runtime — everything must be in the image")
    body = [ln for ln in code if not ln.startswith(("set ", "cd "))]
    if body and all(re.match(r"(echo|printf|cat\s*>)", ln) for ln in body):
        r.warn("hardcoded", "solve.sh only echoes/writes content — must demonstrate the derivation")
    if re.search(r"\bRANDOM\b|random\.(random|choice|shuffle)\(", joined) and "seed" not in joined:
        r.warn("determinism", "randomness without a seed in solve.sh")


# --------------------------------------------------------------------------- rubric.txt


def check_rubric(path: Path, r: Report) -> None:
    if not path.is_file():
        return
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        r.err("encoding", "rubric.txt starts with a UTF-8 BOM — save as UTF-8 without BOM")
    if b"\r\n" in data:
        r.err("encoding", "rubric.txt has CRLF line endings — convert to LF")
    if b"<<REPLACE" in data:
        r.err("placeholder", "skeleton placeholder left in rubric.txt")
    raw_lines = data.decode("utf-8-sig").replace("\r\n", "\n").rstrip("\n").split("\n")
    for n, ln in enumerate(raw_lines, 1):
        if not ln.strip():
            r.err("rubric", f"line {n}: blank line (ship check 52 — no blank lines)")
    lines = [(n, ln.strip()) for n, ln in enumerate(raw_lines, 1) if ln.strip()]
    pos = neg = 0
    negatives = 0
    seen: set[str] = set()
    pattern = re.compile(r"^Agent\s.+,\s([+-])(\d+)$")
    for n, line in lines:
        if line.startswith("#"):
            r.err("rubric", f"line {n}: no headers allowed (ship check 52)")
            continue
        m = pattern.match(line)
        if not m:
            r.err("rubric", f"line {n}: must be 'Agent <does X>, +N' or ', -N': {line[:90]}")
            continue
        sign, value = m.group(1), int(m.group(2))
        if value not in {1, 2, 3, 5}:
            r.err("rubric", f"line {n}: score {value} not allowed (only ±1, ±2, ±3, ±5; never 4)")
        if sign == "-":
            neg += value
            negatives += 1
        else:
            pos += value
        body = line.rsplit(",", 1)[0].lower()
        if body in seen:
            r.err("rubric", f"line {n}: duplicate criterion")
        seen.add(body)
        if re.search(r"/tests\b|test_outputs|test\.sh|instructions?\.md|task\.(toml|yaml)|\boracle\b|\bnop\b", body):
            r.err("rubric", f"line {n}: must not reference /tests, instruction/task files, oracle or NOP")
        elif re.search(r"pytest|unit tests?|test suite", body):
            r.warn("rubric", f"line {n}: mentions tests — only allowed when the task itself is a testing task")
        if re.search(r"\b(does not|doesn't|do not|don't|never|avoids?|without)\b", body):
            r.warn("rubric", f"line {n}: phrase positively and let the sign carry desirability")
        if re.search(r"\b(edge cases|correctly|properly|appropriately|good practices?)\b", body):
            r.warn("rubric", f"line {n}: vague — make it a specific, trace-verifiable action")
    if negatives < 3:
        r.err("rubric", f"only {negatives} negative criteria (need at least 3)")
    if not 10 <= pos <= 40:
        r.err("rubric", f"max cumulative score (sum of positives) is {pos}; must be 10-40")


# --------------------------------------------------------------------------- scrub


def check_scrub(task: Path, extra: list[Path], r: Report) -> None:
    user = getpass.getuser().lower()
    personal = re.compile(r"[A-Za-z]:\\\\?Users\\\\?|/Users/[A-Za-z0-9_.-]+/|/private/tmp/")
    home = re.compile(r"/home/(?!app/|user/|runner/|ubuntu/|node/|agent/)[A-Za-z0-9_.-]+/")
    process = re.compile(r"\b(terminus|caudal|snorkel|chatgpt|claude code|generated by (an? )?(ai|llm|gpt))\b", re.I)
    home_hits: list[str] = []
    for path in all_files(task) + [p for p in extra if p.is_file()]:
        text = read_text(path)
        if text is None:
            continue
        where = rel(task, path) if path.is_relative_to(task) else path.name
        if personal.search(text):
            r.err("scrub", f"{where}: contains a local machine path")
        if re.search(r"\bstb\b", text):
            r.err("scrub", f"{where}: word-boundary 'stb' hit (ship check 85)")
        if "reference_pattern" in text:
            r.err("scrub", f"{where}: reference_pattern pipeline metadata")
        elif home.search(text):
            home_hits.append(where)
        if len(user) >= 4 and re.search(rf"\b{re.escape(user)}\b", text, re.I):
            r.err("scrub", f"{where}: contains the local username '{user}'")
        m = process.search(text)
        if m:
            r.warn("scrub", f"{where}: internal tool/process term '{m.group(0)}'")
    if home_hits:
        shown = ", ".join(home_hits[:3]) + (f" (+{len(home_hits) - 3} more)" if len(home_hits) > 3 else "")
        r.warn("scrub", f"/home/<name>/ paths in {shown} — fine if in-container users, not your machine")


def run_linters(task: Path, r: Report) -> None:
    ruff = shutil.which("ruff")
    if ruff:
        proc = subprocess.run([ruff, "check", str(task)], capture_output=True, text=True)
        if proc.returncode != 0:
            r.err("ruff", (proc.stdout or proc.stderr).strip().splitlines()[-1] + " (run: ruff check --fix <task>)")
    else:
        r.warn("ruff", "ruff not on PATH — install it (py -3 -m pip install ruff) to mirror CI")
    typos = shutil.which("typos")
    if typos:
        proc = subprocess.run([typos, str(task)], capture_output=True, text=True)
        if proc.returncode != 0:
            r.err("typos", f"typos reported issues:\n{proc.stdout.strip()[:1500]}")


def check_task(task: Path, outer: Path | None) -> Report:
    r = Report()
    rubric = (outer or task) / "rubric.txt"
    check_structure(task, outer, r)
    check_toml(task, r)
    check_instruction(task, r)
    check_dockerfile(task, r)
    check_test_sh(task, r)
    check_tests_py(task, r)
    check_solve(task, r)
    check_rubric(rubric, r)
    check_scrub(task, [rubric], r)
    run_linters(task, r)
    return r


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    failed = False
    for arg in argv:
        outer, task = resolve_layout(arg)
        print(f"== tb21_check: {task.name} ==")
        if not task.is_dir():
            print(f"ERROR [structure] not a directory: {task}")
            failed = True
            continue
        r = check_task(task, outer)
        for line in r.errors + r.warns:
            print(line)
        print(f"-- {len(r.errors)} error(s), {len(r.warns)} warning(s)\n")
        failed = failed or bool(r.errors)
    return 1 if failed else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
