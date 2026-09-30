#!/usr/bin/env python3
"""Local static gate for Terminal Bench 4.0 task bundles.

Covers the mechanical parts of the pool's TB 4.0 Master Ship Checklist for the
task itself: instruction.md (0, 3, 5, 11), environment/ and tests/Dockerfile
(13, 16, 18, 24, 25, 26, 37, 38), test.sh and pytest files (39, 49, 50, 54, 56,
57), task.toml (61-65), rubric.txt (67, 69), delivery layout (98) and a
personal-path / stb / canary scrub (99). It does not replace harbor,
tb40_ship_check.py or master_check.py.

Expected layout: <slug>/<slug>/{instruction.md,task.toml,environment,solution,tests}
with <slug>/rubric.txt beside the inner directory.

Usage:
    py -3 tb40/tb40_check.py <slug-dir> [<slug-dir> ...]   (outer or inner path)

Exit code is 1 when any ERROR is reported.
"""

from __future__ import annotations

import ast
import getpass
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

TAXONOMY = {
    "Science": {"Biology", "Chemistry", "Physics", "Earth", "Robotics", "Math", "Linguistics"},
    "Software": {"Algorithms", "Systems", "Databases", "Data engineering", "Frontend"},
    "ML": {"Training", "Inference", "Evaluation", "Kernels"},
    "Operations": {"Finance", "Logistics", "Supply chain", "Claims", "Compliance", "Marketing"},
    "Security": {"Cryptography", "Forensics", "AppSec"},
    "Hardware": {"CAD", "RTL"},
    "Media": {"Music", "Design"},
}
CANONICAL_IMAGES = {
    "public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb",
    "public.ecr.aws/docker/library/node:22-bookworm-slim@sha256:f3a68cf41a855d227d1b0ab832bed9749469ef38cf4f58182fb8c893bc462383",
    "public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac",
    "public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36",
    "public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14",
    "public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c",
    "public.ecr.aws/docker/library/ruby:3.3-slim-bookworm@sha256:e76733e94b3a5893e4a141024ef3a583dc10781dc24becebf74f9c9f9a33e3df",
    "public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d",
    "public.ecr.aws/docker/library/ubuntu:24.04@sha256:0d39fcc8335d6d74d5502f6df2d30119ff4790ebbb60b364818d5112d9e3e932",
}
REQUIRED_FILES = [
    "instruction.md",
    "task.toml",
    "solution/solve.sh",
    "tests/test.sh",
    "tests/Dockerfile",
    "tests/test_outputs.py",
    "tests/test_manifest.json",
]
SUPPORTED_LANGUAGES = {"python", "c", "c++", "cpp", "javascript", "typescript", "java", "go", "rust", "c#", "csharp"}
NETWORK_MODES = {"public", "no-network"}
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
TIMEOUT = 28800
AI_SCAFFOLDING = {"claude.md", "agents.md", "skills.md", ".cursor", ".claude", ".cursorrules", ".aider"}
WRITEUPS = ("difficulty_explanation", "solution_explanation", "verification_explanation", "relevant_experience")
TOP_LEVEL_KEYS = {"name", "artifacts", "metadata", "verifier", "agent", "environment", "solution", "steps",
                  "multi_step_reward_strategy", "source"}
STALE_KEYS = {"schema_version", "version", "task", "codebase_size", "difficulty", "expert_time_estimate_min",
              "junior_time_estimate_min", "milestone", "reference_pattern", "id", "task_id", "task-id",
              "custom_docker_compose"}
TIER_RATE = re.compile(r"\b[0-5]\s*/\s*5\b|\bpass(ed)?[- ]rate\b|\bsolve[ds]?\s+[0-5]\s+(of|out of)\b|\b\d{1,3}\s*%\s*(pass|solve|success)", re.I)
TIER_LABEL = re.compile(r"\b(easy|medium|hard)\s+(difficulty|tier|level)\b|\bdifficulty\s*[:=(]\s*(easy|medium|hard)\b|\b(easy|medium|hard)[- ]tier\b", re.I)
GUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
CANARY = re.compile(r"canary|benchmark data should never", re.I)
STANDARD_DIRS = {"/", "/tmp", "/root", "/usr", "/usr/local", "/opt", "/var", "/etc", "/home", "/srv", "/mnt", "/logs"}
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


def load_toml(task: Path) -> dict:
    try:
        return tomllib.loads((task / "task.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def artifact_sources(data: dict) -> list[str]:
    out = []
    for a in data.get("artifacts", []) or []:
        src = a.get("source") if isinstance(a, dict) else a
        if isinstance(src, str):
            out.append(posixpath.normpath(src))
    return out


# --------------------------------------------------------------------------- structure


def check_structure(task: Path, outer: Path | None, r: Report) -> None:
    if outer is None:
        r.err("layout", f"task must live at <slug>/<slug>/ with rubric.txt in <slug>/ (got {task}) (ship check 98)")
    elif not (outer / "rubric.txt").is_file():
        r.err("structure", f"missing {outer.name}/rubric.txt (beside the inner task directory) (ship check 98)")
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
            r.err("delivery", f"inner task dir may only hold {sorted(INNER_ALLOWED)} — remove/move '{child.name}' (ship check 98)")

    for path in task.rglob("*"):
        if is_junk(path):
            r.err("delivery", f"packaging artifact must be removed: {rel(task, path)} (ship check 98)")
        if path.name.lower() in AI_SCAFFOLDING:
            r.err("ai-scaffolding", f"AI-framework filename not allowed: {rel(task, path)} (ship check 98)")

    for path in all_files(task):
        head = path.read_bytes()[:3]
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
    if slug in {"task", "bundle", "task1", "my-task", "test"} or re.search(
        r"(^|-)(hardened|fixed|patched|final|draft|v\d+|round\d*|copy|tmp|wip)(-|$)", slug
    ):
        r.err("name", f"task name '{slug}' is generic or reveals process history (ship check 98)")


# --------------------------------------------------------------------------- task.toml


def check_toml(task: Path, r: Report) -> dict:
    path = task / "task.toml"
    if not path.is_file():
        return {}
    raw = path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        r.err("toml", f"task.toml does not parse: {exc}")
        return {}

    for key in data:
        if key in STALE_KEYS:
            r.err("toml", f"stale-schema residue: top-level '{key}' (ship check 65)")
        elif key not in TOP_LEVEL_KEYS:
            r.warn("toml", f"unexpected top-level key/table '{key}'")
    if re.search(r"reference_pattern", raw):
        r.err("toml", "[reference_pattern] / generator bookkeeping must not ship (ship check 65)")

    name = data.get("name")
    if not isinstance(name, str) or not name:
        r.err("toml", "top-level name = \"<slug>\" is required, above the first [table] (ship check 61)")
    elif name != task.name:
        r.err("toml", f"name '{name}' must equal the task directory name '{task.name}' (ship check 61)")

    verifier = data.get("verifier", {})
    if "artifacts" in verifier:
        r.err("toml", "artifacts is nested under [verifier] — Harbor silently drops it; make it a top-level key (ship check 37/61)")
    arts = data.get("artifacts")
    if not isinstance(arts, list) or not arts:
        r.err("toml", "top-level artifacts = [...] listing every path the verifier needs is required (ship check 37/61)")

    meta = data.get("metadata", {})
    for key in ("author_name", "author_email"):
        if key not in meta:
            r.err("toml", f"[metadata].{key} missing ('anonymous') (ship check 61)")
    for key in ("category", "subcategory", "tags", "languages", "expert_time_estimate_hours", *WRITEUPS):
        if key not in meta:
            r.err("toml", f"[metadata].{key} is required (ship check 61)")
    for key in STALE_KEYS & set(meta):
        r.err("toml", f"stale-schema residue: [metadata].{key} (ship check 62/65)")
    for tbl_name, tbl in data.items():
        if isinstance(tbl, dict) and tbl_name != "metadata":
            for key in {"difficulty", "codebase_size"} & set(tbl):
                r.err("toml", f"stale-schema residue: [{tbl_name}].{key} (ship check 62/65)")

    category, sub = meta.get("category"), meta.get("subcategory")
    if category is not None:
        if category not in TAXONOMY:
            r.err("toml", f"category '{category}' is not a TAXONOMY.yaml domain {sorted(TAXONOMY)} (ship check 61)")
        elif sub is not None and sub not in TAXONOMY[category]:
            r.err("toml", f"subcategory '{sub}' is not a {category} subarea {sorted(TAXONOMY[category])} (ship check 61)")
    if isinstance(category, list) or isinstance(sub, list):
        r.err("toml", "category and subcategory must be exactly one string each (ship check 61)")

    tags = meta.get("tags")
    if tags is not None and (not isinstance(tags, list) or not 3 <= len(tags) <= 6):
        r.err("toml", "tags must be a list of 3-6 specific keywords (ship check 61)")
    languages = meta.get("languages")
    if languages is not None:
        if not isinstance(languages, list) or not languages:
            r.err("toml", "languages must be a non-empty list (ship check 61)")
        else:
            if "python" in [str(x).lower() for x in languages] and len(languages) > 1:
                r.warn("toml", "list python only if it is the primary language (pytest tests don't count)")
            if not any(str(x).lower() in SUPPORTED_LANGUAGES for x in languages):
                r.warn("toml", f"languages {languages} include none of the supported primary languages (Python, C, C++, JavaScript, TypeScript, Java, Go, Rust, C#)")
    hours = meta.get("expert_time_estimate_hours")
    if hours is not None and (not isinstance(hours, (int, float)) or hours <= 0):
        r.err("toml", "expert_time_estimate_hours must be a positive number (ship check 61)")
    for key in WRITEUPS:
        val = meta.get(key)
        if val is None:
            continue
        if not isinstance(val, str) or len(val.split()) < 8:
            r.err("toml", f"[metadata].{key} must be a substantive write-up, not placeholder text (ship check 61)")
        elif key == "relevant_experience" and re.search(r"interested in (ai|ml)|passionate about", val, re.I):
            r.err("toml", "relevant_experience is generic — describe real, relevant professional background (ship check 61)")
        elif key != "relevant_experience" and TIER_RATE.search(val):
            r.err("toml", f"[metadata].{key} contains a pass count / rate '{TIER_RATE.search(val).group(0).strip()}' (ship check 62)")
        elif key != "relevant_experience" and TIER_LABEL.search(val):
            r.err("toml", f"[metadata].{key} contains a tier label '{TIER_LABEL.search(val).group(0).strip()}' (ship check 62)")

    if verifier.get("environment_mode") != "separate":
        r.err("toml", f"[verifier].environment_mode must be \"separate\" (is {verifier.get('environment_mode')!r}) (ship check 63)")
    for tbl in ("agent", "verifier"):
        value = data.get(tbl, {}).get("timeout_sec")
        if value != TIMEOUT:
            r.err("toml", f"[{tbl}].timeout_sec is {value}; must be {TIMEOUT} (ship check 63)")

    env = data.get("environment", {})
    mode = env.get("network_mode")
    if mode not in NETWORK_MODES:
        r.err("toml", f"[environment].network_mode must be \"public\" (default) or \"no-network\" (is {mode!r}) (ship check 64)")
    elif mode == "no-network":
        r.warn("toml", "network_mode = \"no-network\": allowed only when public internet would let the agent skip the actual work — sign off check 64 with that reason (ship check 64)")
    if "allow_internet" in env:
        r.err("toml", "[environment].allow_internet is removed in TB 4.0 — use network_mode only (ship check 64/65)")
    for key in ("cpus", "memory_mb", "storage_mb"):
        if key not in env:
            r.err("toml", f"[environment].{key} is required (~2 CPUs, ~8192 MB memory, ~10240 MB storage)")
    if isinstance(env.get("cpus"), (int, float)) and env["cpus"] > 2:
        r.warn("toml", f"[environment].cpus = {env['cpus']} exceeds the ~2-core compute envelope")
    if isinstance(env.get("memory_mb"), (int, float)) and env["memory_mb"] > 8192:
        r.warn("toml", f"[environment].memory_mb = {env['memory_mb']} exceeds the ~8 GB compute envelope")
    if isinstance(env.get("storage_mb"), (int, float)) and env["storage_mb"] > 10240:
        r.warn("toml", f"[environment].storage_mb = {env['storage_mb']} exceeds the ~10 GB compute envelope")
    if "gpus" in env:
        r.err("toml", "[environment].gpus — no GPU is required or supported in TB 4.0")

    compose = task / "environment" / "docker-compose.yaml"
    if not compose.is_file():
        compose = task / "environment" / "docker-compose.yml"
    services = 0
    if compose.is_file():
        text = compose.read_text(encoding="utf-8")
        block = re.search(r"^services:\s*\n((?:[ \t]+.*\n?|\s*\n)*)", text, re.M)
        services = len(re.findall(r"^[ ]{2}[A-Za-z0-9_.-]+:\s*$", block.group(1), re.M)) if block else 0
    multi = meta.get("is_multi_container")
    if services > 1 and multi is not True:
        r.err("toml", f"compose defines {services} services: set [metadata].is_multi_container = true (ship check 65)")
    if services <= 1 and multi is not None:
        r.err("toml", "single-container task must omit is_multi_container entirely (ship check 65)")

    if re.search(r"[A-Za-z]:\\|/Users/|/private/tmp/|/home/", raw):
        r.err("scrub", "task.toml contains a local machine path (ship check 65)")
    if CANARY.search(raw) or GUID.search(raw):
        r.err("scrub", "task.toml contains a canary / GUID-shaped string (ship check 99)")
    return data


# --------------------------------------------------------------------------- instruction.md


def check_instruction(task: Path, r: Report) -> None:
    path = task / "instruction.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    low = text.lower()

    if CANARY.search(text) or GUID.search(text):
        r.err("instruction", "canary / GUID-shaped string found — never add one (ship check 11)")
    slug = task.name.lower()
    if slug in low or slug.replace("-", " ") in low:
        r.err("instruction", "the task's own name/slug appears in the instruction.md body")
    if re.search(r"\b(grader|graded by|pytest|test_outputs|the test suite|the verifier)\b|/tests\b|/opt/verifier", low):
        r.err("instruction", "mentions grading tooling (grader/test suite/the verifier/pytest//tests//opt/verifier) (ship check 5)")
    if re.search(r"\bhidden tests?\b|\btest suite\b", low):
        r.warn("instruction", "mentions tests — keep framing inside the task fiction (ship check 5)")
    if re.search(r"\boffline\b|\bno (internet|network)\b|without (internet|network)|(don't|do not|never) (use|access|reach) the (internet|network)", low):
        if load_toml(task).get("environment", {}).get("network_mode") != "no-network":
            r.err("instruction", "tells the agent to stay offline while network_mode is not \"no-network\" (ship check 64)")
    if re.search(r"^#{1,6}\s*detection guidance|\bdetection guidance\b", low, re.M):
        r.err("instruction", "\"Detection Guidance\" section — states the how, not the what (ship check 3)")
    bold = re.findall(r"\*\*[^*\n]+\*\*", text)
    if bold:
        r.warn("instruction", f"bold text {bold[:3]} — bold spotlighting the key value is an answer leak / AI-prose tell (ship check 0)")
    if re.search(r"you have \d+ seconds to complete", low):
        r.warn("instruction", "upstream 'You have N seconds…' suffix is not part of the pool format — remove it")
    m = TIER_RATE.search(text) or TIER_LABEL.search(text)
    if m:
        r.err("instruction", f"tier / pass-rate language '{m.group(0).strip()}' (ship check 62)")
    outside_ticks = re.sub(r"`[^`\n]*`", " ", text)
    bare = sorted(set(re.findall(r"(?<![\w`/.:-])(/(?:app|data|opt|etc|var|srv|usr|home|tmp|root|workspace|logs|output|mnt|repo|src)(?:/[\w.@+-]+)*/?)", outside_ticks)))
    for p in bare[:10]:
        r.err("absolute-path", f"absolute path {p} must be written in backticks (ship check 0)")
    if re.search(r"you are an? (expert|senior|experienced)|your (goal|task) is to|i hope this helps", low):
        r.warn("instruction", "reads LLM-generated ('You are an expert…' / 'Your goal is to…') (ship check 0)")
    if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", text):
        r.err("instruction", "emoji found (ship check 0)")

    words = len(re.findall(r"\S+", text))
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    headings = len(re.findall(r"^\s{0,3}#{1,6}\s", text, re.M))
    bullets = len(re.findall(r"^\s*(?:[-*+]|\d+[.)])\s", text, re.M))
    numbered = len(re.findall(r"^\s*\d+[.)]\s", text, re.M))
    bold = len(re.findall(r"\*\*[^*]+\*\*|__[^_]+__", text))
    if words > 400 or len(paragraphs) > 6:
        r.warn("instruction", f"{words} words / {len(paragraphs)} blocks — guide is ~2 short paragraphs; fine only if the problem itself needs it, not step lists (ship check 0)")
    if headings:
        r.warn("instruction", f"{headings} markdown heading(s) — reads like documentation, not a prompt (ship check 0)")
    if bullets > 20:
        r.warn("instruction", f"{bullets} bullets — guide is up to ~20 (ship check 0)")
    if numbered >= 4:
        r.warn("instruction", f"{numbered} numbered items — looks like a step list (ship check 0/3)")
    if bold >= 3:
        r.warn("instruction", f"{bold} bold markers — bold solution details read as hints (ship check 10)")
    if re.search(r"(?i)\b(step \d|first,? (run|use|open)|hint|look for)\b", text):
        r.warn("instruction", "possible step-by-step / hint language (ship check 3/10)")

    tokens = text.replace("`", " ").split()
    flagged: set[str] = set()
    for tok in tokens:
        t = tok.strip("`\"'(),;:!?[]{}<>*")
        t = t.rstrip(".")
        if not t or "://" in t or t.startswith("/") or t in flagged:
            continue
        if t.startswith("~/"):
            flagged.add(t)
            r.err("absolute-path", f"home-relative path '{t}' — use an absolute path (ship check 0)")
        elif "/" in t and (
            t.startswith(("./", "../")) or re.search(r"\.[A-Za-z0-9]{1,6}$", t.split("/")[-1])
        ):
            flagged.add(t)
            r.err("absolute-path", f"relative path '{t}' — use an absolute path like /app/{t.lstrip('./')} (ship check 0)")


# --------------------------------------------------------------------------- Dockerfiles / environment


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
        r.warn("pinned-images", f"{where}: image '{image}' uses a build arg — cannot verify the digest pin (ship check 26)")
        return
    if "@sha256:" not in image:
        r.err("pinned-images", f"{where}: image '{image}' is not digest-pinned with @sha256:<digest> (ship check 26)")


def split_commands(run: str) -> list[str]:
    return [c.strip() for c in re.split(r"&&|\|\||;|\|", run) if c.strip()]


def check_pip(cmd: str, ctx_dir: Path, where: str, r: Report) -> None:
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
            req = ctx_dir / Path(tokens[i + 1]).name
            matches = [req] if req.is_file() else list(ctx_dir.rglob(Path(tokens[i + 1]).name))
            for req_file in matches[:1]:
                check_requirements(req_file, ctx_dir, r)
            continue
        if tok in {"-f", "--find-links", "-i", "--index-url", "--extra-index-url", "-t", "--target", "--prefix"}:
            skip_next = True
            continue
        if tok.startswith("-") or tok.endswith(".whl") or tok.startswith(("/", ".")) or "://" in tok:
            continue
        if "==" not in tok:
            r.err("pinned-deps", f"{where}: pip package '{tok}' is not pinned with == (ship check 26/38)")


def check_requirements(path: Path, ctx_dir: Path, r: Report) -> None:
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.split("#", 1)[0].strip()
        if not s or s.startswith(("-", "--")):
            continue
        if "==" not in s:
            r.err("pinned-deps", f"{path.relative_to(ctx_dir.parent).as_posix()}:{n} '{s}' is not pinned with == (ship check 26/38)")


def check_one_dockerfile(task: Path, df: Path, agent_image: bool, r: Report) -> list[tuple[str, str]]:
    ctx_dir = df.parent
    where = rel(task, df)
    text = df.read_text(encoding="utf-8")
    instrs = dockerfile_instructions(text)
    stages: dict[str, str] = {}
    final_base = None
    for op, args in instrs:
        if op != "FROM":
            continue
        if re.search(r"--platform", args):
            r.err("platform", f"{where}: FROM --platform pin is not allowed (ship check 26)")
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
            r.warn("sanctioned-base", f"{where}: canonical family but not the canonical digest: {final_base} (ship check 26)")
        else:
            justified = re.search(r"#.*(justif|canonical|non-canonical|base image)", text, re.I)
            if justified:
                r.warn("sanctioned-base", f"{where}: non-canonical final base {final_base} — reviewer will judge the justification (ship check 26)")
            else:
                r.err("sanctioned-base", f"{where}: non-canonical final base {final_base} with no justification comment (ship check 26)")

    runs = [args for op, args in instrs if op == "RUN"]
    all_run = "\n".join(runs)
    if agent_image:
        if not re.search(r"\btmux\b", all_run) or not re.search(r"\basciinema\b", all_run):
            r.err("runtime", f"{where}: tmux and asciinema must be installed in the agent image (ship check 26)")
    if not any(op == "WORKDIR" for op, _ in instrs):
        r.warn("workdir", f"{where}: no WORKDIR set (test.sh refuses to run from /)")

    apt_updates = 0
    for run in runs:
        if re.search(r"apt-get\s+(upgrade|dist-upgrade)", run):
            r.warn("apt", f"{where}: never run apt-get upgrade")
        if re.search(r"apt-get\s+update", run):
            apt_updates += 1
        am = re.search(r"apt-get\s+install\b(.*)", run)
        if am:
            if "--no-install-recommends" not in run:
                r.warn("apt", f"{where}: apt-get install without --no-install-recommends")
            if "/var/lib/apt/lists" not in run:
                r.warn("apt", f"{where}: apt lists not removed in the same RUN")
            pkgs_part = re.split(r"&&|;|\|", am.group(1))[0]
            for tok in pkgs_part.split():
                if not tok.startswith("-") and re.fullmatch(r"[a-z0-9][a-z0-9.+-]*=[^\s]+", tok):
                    r.err("apt-pin", f"{where}: apt package '{tok}' is version-pinned — apt installs must be unpinned (ship check 26)")
        if re.search(r"(curl|wget)[^|]*\|\s*(ba|z)?sh", run):
            r.warn("reproducible", f"{where}: curl|sh — pin version and verify sha256")
        elif re.search(r"\b(curl|wget)\b.*https?://", run):
            r.warn("web-fetch", f"{where}: downloads from the web at build time — only packages allowed; vendor data instead")
        if re.search(r"git\s+clone", run) and "checkout" not in run:
            r.warn("reproducible", f"{where}: git clone without pinning a commit")
        if re.search(r"<<-?\s*['\"]?[A-Z_]+", run):
            r.warn("heredoc", f"{where}: heredoc in RUN — ship files and COPY them")
        if re.search(r"\b(chmod|chown)\s+-R\b", run):
            r.warn("permissions", f"{where}: recursive chmod/chown — use COPY --chmod/--chown")
        if agent_image and re.search(r"(mkdir|chown|chmod|rm|touch|cp|mv|ln)[^&;|]*\s/(tests|solution|oracle|logs/verifier|logs/artifacts)\b", run):
            r.err("reserved-dirs", f"{where}: must not create/modify /tests, /solution, /oracle, /logs/verifier or /logs/artifacts (ship check 24)")
        for cmd in split_commands(run):
            check_pip(cmd, ctx_dir, where, r)
            m = re.search(r"\bnpm\s+(install|i)\b(.*)", cmd)
            if m:
                pkgs = [t for t in m.group(2).split() if not t.startswith("-")]
                if not pkgs:
                    r.warn("pinned-deps", f"{where}: prefer 'npm ci' with package-lock.json over 'npm install'")
                for p in pkgs:
                    if p.count("@") < (2 if p.startswith("@") else 1):
                        r.err("pinned-deps", f"{where}: npm package '{p}' is not version-pinned (ship check 26)")
            if re.search(r"\bgo\s+install\s+\S+@latest", cmd):
                r.err("pinned-deps", f"{where}: go install @latest is unpinned (ship check 26)")
            if re.search(r"\bcargo\s+install\b", cmd) and "--version" not in cmd and "--locked" not in cmd:
                r.warn("pinned-deps", f"{where}: cargo install without --version/--locked")
            if re.search(r"\bgem\s+install\b", cmd) and not re.search(r"\s(-v|--version)\s", cmd):
                r.warn("pinned-deps", f"{where}: gem install without -v")
    if apt_updates > 1:
        r.warn("apt", f"{where}: {apt_updates} separate apt-get update transactions — consolidate")

    if agent_image:
        for op, args in instrs:
            if op in {"COPY", "ADD"}:
                if "--from" in args:
                    continue
                srcs = [t for t in args.split() if not t.startswith("--")][:-1]
                dest = ([t for t in args.split() if not t.startswith("--")] or [""])[-1]
                for s in srcs:
                    norm = s.strip("\"'[],").lstrip("./")
                    if re.match(r"(tests|solution)(/|$)", norm) or "/tests" in s or "/solution" in s:
                        r.err("tests-in-image", f"{where}: {op} {args} copies tests/solution into the image (ship check 24)")
                    if s in {".", "./"}:
                        r.warn("layers", f"{where}: '{op} . ' copies the whole context — prefer narrow COPY")
                if re.match(r"/(tests|solution|oracle|logs/verifier|logs/artifacts)\b", dest.strip("\"'")):
                    r.err("reserved-dirs", f"{where}: {op} into reserved path {dest} (ship check 24)")
        if re.search(r"solve\.sh|test_outputs\.py|tests/test\.sh", text):
            r.err("dockerfile-references", f"{where}: references solution/test files (ship check 24)")
    return instrs


def created_paths(instrs: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    wd = "/"
    for op, args in instrs:
        if op == "WORKDIR":
            wd = posixpath.normpath(posixpath.join(wd, args.strip().strip("\"'")))
            out.add(wd)
        elif op in {"COPY", "ADD"}:
            toks = [t.strip("\"'[],") for t in args.split() if not t.startswith("--")]
            if len(toks) >= 2:
                out.add(posixpath.normpath(posixpath.join(wd, toks[-1])))
        elif op == "RUN":
            for m in re.finditer(r"\bmkdir\s+(?:-\S+\s+)*((?:[^\s;&|]+\s*)+)", args):
                for p in m.group(1).split():
                    if p.startswith("/"):
                        out.add(posixpath.normpath(p))
    grown = set(out)
    for p in out:
        while p not in ("/", ""):
            p = posixpath.dirname(p)
            grown.add(p)
    return grown


def check_verifier_dockerfile(task: Path, data: dict, r: Report) -> None:
    df = task / "tests" / "Dockerfile"
    if not df.is_file():
        return
    instrs = check_one_dockerfile(task, df, agent_image=False, r=r)
    copies_tests = any(
        op in {"COPY", "ADD"} and re.match(r"^(?:--\S+\s+)*\.\s+/tests/?$", args.strip())
        for op, args in instrs
    )
    if not copies_tests:
        r.err("verifier-image", "tests/Dockerfile must `COPY . /tests/` — Harbor does not upload tests/ in separate mode (ship check 37)")
    made = created_paths(instrs)
    for src in artifact_sources(data):
        if not src.startswith("/"):
            continue
        parent = posixpath.dirname(src) or "/"
        if parent not in made and parent not in STANDARD_DIRS:
            r.err("verifier-image", f"artifact {src}: parent {parent} is not created in tests/Dockerfile (mkdir -p / WORKDIR) (ship check 37)")
        elif not posixpath.splitext(src)[1] and src not in made:
            r.warn("verifier-image", f"artifact dir {src} is not pre-created in tests/Dockerfile — add `RUN mkdir -p {src}` (ship check 37)")
    run_text = "\n".join(a for o, a in instrs if o == "RUN")
    if not re.search(r"\bpytest==", run_text) and not re.search(r"pytest==", read_text(task / "tests" / "requirements.txt") or ""):
        r.err("verifier-image", "tests/Dockerfile must bake pytest at an exact version (ship check 38)")
    if not re.search(r"pytest-json-ctrf==", run_text):
        r.warn("verifier-image", "tests/Dockerfile does not bake pytest-json-ctrf== (test.sh writes ctrf.json with --ctrf)")


def check_environment(task: Path, r: Report) -> None:
    env = task / "environment"
    dockerfiles = sorted(env.glob("Dockerfile*")) if env.is_dir() else []
    for df in dockerfiles:
        check_one_dockerfile(task, df, agent_image=True, r=r)

    for compose in [env / "docker-compose.yaml", env / "docker-compose.yml"]:
        if not compose.is_file():
            continue
        where = rel(task, compose)
        text = compose.read_text(encoding="utf-8")
        if re.search(r"privileged:\s*true", text) or re.search(r"SYS_ADMIN|NET_ADMIN|SYS_MODULE|docker\.sock", text):
            r.err("privileged", f"{where}: privileged mode / dangerous capability / docker.sock (ship check 26)")
        if re.search(r"context:\s*\.\.", text):
            r.err("context", f"{where}: build context outside environment/")
        if re.search(r":\s*/(logs/verifier|logs/artifacts|tests|solution|oracle)\b", text):
            r.err("reserved-mounts", f"{where}: mounts a reserved path (ship check 24)")
        if re.search(r"platform:", text):
            r.err("platform", f"{where}: platform pin is not allowed (ship check 26)")
        for image in re.findall(r"^\s*image:\s*['\"]?([^\s'\"]+)", text, re.M):
            check_image_pin(image, where, r)

    if not env.is_dir():
        return
    files = all_files(env)
    total = sum(p.stat().st_size for p in files)
    if total > 100 * MIB:
        r.err("context-size", f"environment/ is {total / MIB:.1f} MiB (max 100) (ship check 26)")
    for p in files:
        if p.stat().st_size > 50 * MIB:
            r.err("context-size", f"{rel(task, p)} is over 50 MiB (ship check 26)")
    if not (env / ".dockerignore").is_file():
        r.warn("dockerignore", "environment/.dockerignore missing (template in tb40/skeleton)")
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
                    r.warn("defect-tell", f"{rel(task, p)}:{n} grep hit (ship check 13 — remove or justify): {line.strip()[:100]}")
            if p in files and re.search(r"\b(decoy|red[- ]herring)\b", line, re.I):
                r.err("decoy-label", f"{rel(task, p)}:{n} labels a decoy as a decoy (ship check 25)")
            if p in files and (CANARY.search(line) or GUID.search(line)):
                r.warn("canary", f"{rel(task, p)}:{n} canary / GUID-shaped string — confirm it is real project data, not training-canary material (ship check 99)")
    if hits > 15:
        r.warn("defect-tell", f"... {hits - 15} more grep hits")

    common = {"db", "io", "ui", "os", "go", "js", "ts", "v1", "v2", "v3", "api", "cmd", "pkg", "lib", "src", "bin",
              "etc", "app", "web", "net", "log", "tmp", "doc", "img", "css", "sql", "cli", "ci", "gc", "id", "ip", "rpc"}
    for p in env.rglob("*"):
        stem = p.stem.lower() if p.is_file() else p.name.lower()
        if stem not in common and re.fullmatch(r"[a-z]{1,3}\d{1,2}|[a-z]{1,2}", stem):
            r.warn("naming", f"{rel(task, p)}: opaque short name — must be decodable (ship check 16)")

    ref_exts = {".md", ".json", ".yaml", ".yml", ".toml", ".csv", ".txt", ".sh", ".conf", ".ini", ".sql", ".xml", ".cfg", ".tsv", ".env.example"}
    bundle_texts = {p: read_text(p) or "" for p in all_files(task) if not is_junk(p)}
    for p in files:
        if p.suffix.lower() not in ref_exts or p.name in {".dockerignore", "README.md", "go.sum", "package-lock.json"}:
            continue
        if not any(p.name in text for q, text in bundle_texts.items() if q != p):
            r.warn("unreferenced", f"{rel(task, p)} is referenced nowhere else in the bundle (ship check 18)")


# --------------------------------------------------------------------------- tests / solution


def check_test_sh(task: Path, r: Report) -> None:
    path = task / "tests" / "test.sh"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))
    if not text.startswith("#!"):
        r.warn("test-sh", "missing shebang")
    if "/logs/verifier/reward.txt" not in code:
        r.err("test-sh", "never writes /logs/verifier/reward.txt (ship check 39)")
    if "mkdir -p /logs/verifier" not in code:
        r.warn("test-sh", "add 'mkdir -p /logs/verifier' before running pytest (ship check 39)")
    if not re.search(r"chmod\s+0?755\s+/logs/verifier", code):
        r.warn("test-sh", "add 'chmod 0755 /logs/verifier' so sandboxed agent code cannot write reward/ctrf (ship check 54)")
    if not re.search(r"\bpytest\b", code):
        r.err("test-sh", "does not run pytest (all verifiers must be Python pytest)")
    if re.search(r"^\s*set\s+-[a-zA-Z]*e", code, re.M) or "errexit" in code:
        r.err("test-sh", "set -e can exit before the reward is written — use 'set -uo pipefail' (ship check 39)")
    if re.search(r"\buvx\b|\bnpm\s+(install|i|ci)\b|\bcurl\b|\bwget\b|git\s+clone|apt-get|apk\s+add|cargo\s+(fetch|install)|go\s+(get|install|mod\s+download)|mvn\s+dependency", code):
        r.err("test-sh", "installs/fetches at runtime — bake verifier deps into tests/Dockerfile (ship check 38)")
    for m in re.finditer(r"\bpip3?\s+install\b[^\n]*", code):
        r.err("test-sh", f"pip install at runtime: '{m.group(0)[:60]}' — bake it into tests/Dockerfile (ship check 38)")
    if re.search(r"\bgo\s+test\b|\bmvn\s+test\b|\bgradle\w*\s+test\b|\bnpm\s+test\b|\bjest\b|\bcargo\s+test\b", code):
        r.err("test-sh", "delegates to a non-pytest test framework")
    if "/oracle" in code or "EVAL_IS_ORACLE" in code or re.search(r"\bJOB_NAME\b|\bTRIAL_NAME\b|\bAGENT_NAME\b", code):
        r.err("test-sh", "oracle/identity-specific logic — oracle and agent must be verified identically (ship check 57)")
    if re.search(r"\$TEST_DIR\b|\$\{TEST_DIR\}", code) and not re.search(r"TEST_DIR=\"?\$\{TEST_DIR:-", code):
        r.err("test-sh", "TEST_DIR used without a default (TEST_DIR=\"${TEST_DIR:-/tests}\")")
    for m in re.finditer(r"reward\.txt", code):
        line = code[code.rfind("\n", 0, m.start()) + 1: code.find("\n", m.end()) if code.find("\n", m.end()) >= 0 else None]
        if re.search(r"echo\s+(?![01]\s*>)", line) and ">" in line:
            r.err("test-sh", f"reward must be exactly 0 or 1: `{line.strip()[:80]}` (ship check 57)")
    lines = [ln.strip() for ln in code.splitlines() if ln.strip()]
    if not lines or lines[-1] != "exit 0":
        r.err("test-sh", "test.sh must end with `exit 0` — the reward file decides pass/fail, not the exit status (ship check 39)")
    first_reward = re.search(r"echo\s+([01])\s*>\s*/logs/verifier/reward\.txt", code)
    if not first_reward or first_reward.group(1) != "0" or code.find("pytest") < first_reward.start():
        r.warn("test-sh", "initialize reward.txt to 0 before anything can fail (echo 0 > /logs/verifier/reward.txt right after mkdir)")
    if "TBENCH_TEST_ID" not in code:
        r.err("test-sh", "no TBENCH_TEST_ID selector — run everything when unset, exactly the manifest ids when set, reject unknown ids (see tb40/skeleton/task/tests/test.sh) (ship check 39)")
    elif not re.search(r"TBENCH_TEST_ID=\"?\$\{TBENCH_TEST_ID:-", code):
        r.err("test-sh", "TBENCH_TEST_ID read without a default (TBENCH_TEST_ID=\"${TBENCH_TEST_ID:-}\") — set -u aborts before the reward write (ship check 39)")
    elif "test_manifest.json" not in code:
        r.err("test-sh", "TBENCH_TEST_ID is not validated against /tests/test_manifest.json — unknown ids must be rejected (ship check 39)")


def check_manifest(task: Path, r: Report) -> None:
    tests_dir = task / "tests"
    path = tests_dir / "test_manifest.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        r.err("manifest", f"tests/test_manifest.json is not valid JSON: {exc} (ship check 53)")
        return
    entries = data.get("tests") if isinstance(data, dict) else None
    if not isinstance(entries, list) or not entries:
        r.err("manifest", 'tests/test_manifest.json must be {"tests": [{"id": "test_outputs.py::test_x", "description": "..."}, ...]} (ship check 53)')
        return
    ids: list[str] = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict) or not isinstance(e.get("id"), str):
            r.err("manifest", f"tests/test_manifest.json entry {i} has no string id (ship check 53)")
            continue
        ids.append(e["id"])
        desc = e.get("description")
        if not isinstance(desc, str) or len(desc.split()) < 3 or "<<REPLACE" in desc:
            r.err("manifest", f"{e['id']}: description missing or placeholder (ship check 43)")
    for dup in sorted({x for x in ids if ids.count(x) > 1}):
        r.err("manifest", f"duplicate manifest id {dup} (ship check 53)")
    collected: set[str] = set()
    for py in sorted(tests_dir.rglob("test_*.py")):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        prefix = py.relative_to(tests_dir).as_posix()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                collected.add(f"{prefix}::{node.name}")
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name.startswith("test"):
                        collected.add(f"{prefix}::{node.name}::{sub.name}")
    for missing in sorted(collected - set(ids)):
        r.err("manifest", f"{missing} is collected by pytest but absent from tests/test_manifest.json (ship check 53)")
    for extra in sorted(set(ids) - collected):
        r.err("manifest", f"manifest id {extra} matches no test function (must equal the CTRF name 'file.py::test_name') (ship check 53)")


def check_tests_py(task: Path, r: Report) -> None:
    tests_dir = task / "tests"
    if not tests_dir.is_dir():
        return
    total = 0
    all_test_src = "\n".join(read_text(p) or "" for p in tests_dir.rglob("*.py"))
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
                    r.err("docstrings", f"{where}:{node.lineno} {node.name} needs an informative docstring (ship check 43)")
        if re.search(r"time\.(time|perf_counter|monotonic)\(\)", src) and re.search(r"assert[^\n]*(elapsed|duration|latency|throughput|\bms\b|seconds|per_sec|qps|p9\d)", src, re.I):
            r.err("latency", f"{where}: wall-clock latency/throughput assertion — absolute ban (ship check 56)")
        for url in re.findall(r"https?://([^/\s\"']+)", src):
            if not re.match(r"(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])", url):
                r.warn("network", f"{where}: references external host {url} — tests must not depend on the network (ship check 38)")
        if re.search(r"/oracle\b|EVAL_IS_ORACLE", src):
            r.err("tests", f"{where}: oracle-specific branching (ship check 57)")
        if re.search(r"^\s*@pytest\.fixture\([^)]*autouse\s*=\s*True[^)]*scope\s*=\s*[\"']session|scope\s*=\s*[\"']session[^)]*autouse\s*=\s*True", src, re.M):
            r.warn("tests", f"{where}: session-scoped autouse fixture — if it asserts, every NOP row becomes an infra error (ship check 76)")
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Add)
                and isinstance(node.left, ast.Constant)
                and isinstance(node.left.value, str)
                and isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, str)
            ):
                r.err("obfuscation", f"{where}:{node.lineno} string-literal concatenation (ship check 49)")
            if isinstance(node, ast.Call):
                fname = ast.unparse(node.func)
                if fname in {"subprocess.run", "subprocess.Popen", "subprocess.check_output", "subprocess.call", "subprocess.check_call", "os.system"}:
                    kws = {k.arg for k in node.keywords}
                    if "user" not in kws:
                        r.warn("sandbox", f"{where}:{node.lineno} {fname}() without user= — if it runs agent-produced code it must go through the sandbox helper (ship check 54)")
                    elif not {"env", "start_new_session"} <= kws:
                        r.warn("sandbox", f"{where}:{node.lineno} {fname}() drops privileges but lacks env= / start_new_session= (ship check 54)")
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("test"):
                if len(re.findall(rf"\b{re.escape(node.name)}\b", all_test_src)) <= 1:
                    r.err("dead-code", f"{where}:{node.lineno} helper '{node.name}' is never used (ship check 50)")
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    name = (alias.asname or alias.name).split(".")[0]
                    if name != "*" and len(re.findall(rf"\b{re.escape(name)}\b", src)) <= 1:
                        r.err("dead-code", f"{where}:{node.lineno} import '{name}' is unused (ship check 50)")
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
    if re.search(r"(scenario|case)_?id\s*==|if \[\[?\s*\"?\$\{?(SCENARIO|CASE)", joined, re.I):
        r.warn("solve", "solve.sh branches on a scenario/case id — confirm it computes rather than returns constants (ship check 31)")


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
            r.err("rubric", f"line {n}: blank line (ship check 67)")
    lines = [(n, ln.strip()) for n, ln in enumerate(raw_lines, 1) if ln.strip()]
    pos = 0
    negatives = 0
    seen: set[str] = set()
    pattern = re.compile(r"^Agent\s.+,\s([+-])(\d+)$")
    for n, line in lines:
        if line.startswith("#"):
            r.err("rubric", f"line {n}: no headers allowed (ship check 67)")
            continue
        m = pattern.match(line)
        if not m:
            r.err("rubric", f"line {n}: must be exactly 'Agent <behavior>, +N' or ', -N' (explicit sign): {line[:90]} (ship check 67)")
            continue
        sign, value = m.group(1), int(m.group(2))
        if value not in {1, 2, 3, 5}:
            r.err("rubric", f"line {n}: magnitude {value} not allowed (only 1, 2, 3, 5; never 4) (ship check 67)")
        if sign == "-":
            negatives += 1
        else:
            pos += value
        body = line.rsplit(",", 1)[0].lower()
        if body in seen:
            r.err("rubric", f"line {n}: duplicate criterion (ship check 69)")
        seen.add(body)
        if re.search(r"/tests\b|test_outputs|test\.sh|instructions?\.md|task\.(toml|yaml)|\boracle\b|\bnop\b|\btest_[a-z0-9_]+\b", body):
            r.err("rubric", f"line {n}: must not cite tests, instruction/task files, oracle or NOP (ship check 67)")
        elif re.search(r"pytest|unit tests?|test suite", body):
            r.warn("rubric", f"line {n}: mentions tests — only allowed when the task itself is a testing task")
        if re.search(r"\bfile (exists|is present|is created)\b|\b(creates|produces|writes) (the |an? )?(output )?file\b|\bexistence of\b", body):
            r.warn("rubric", f"line {n}: grades file existence — rubric lines grade conduct, never artifact existence (ship check 67)")
        if re.search(r"\b(does not|doesn't|do not|don't|never|avoids?|without)\b", body):
            r.warn("rubric", f"line {n}: phrase positively and let the sign carry desirability")
        if re.search(r"\b(edge cases|correctly|properly|appropriately|good practices?)\b", body):
            r.warn("rubric", f"line {n}: vague — make it a specific, trace-verifiable action")
    if negatives < 1:
        r.err("rubric", "no negative criterion (at least one required) (ship check 67)")
    if not 10 <= pos <= 40:
        r.err("rubric", f"sum of positives is {pos}; must be 10-40 (ship check 67)")


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
            r.err("scrub", f"{where}: contains a local machine path (ship check 99)")
        if re.search(r"\bstb\b", text):
            r.err("scrub", f"{where}: word-boundary 'stb' hit (ship check 99)")
        if "reference_pattern" in text:
            r.err("scrub", f"{where}: reference_pattern pipeline metadata (ship check 65)")
        elif home.search(text):
            home_hits.append(where)
        if len(user) >= 4 and re.search(rf"\b{re.escape(user)}\b", text, re.I):
            r.err("scrub", f"{where}: contains the local username '{user}' (ship check 99)")
        if (path.name == "rubric.txt" or path.is_relative_to(task / "tests") or path.is_relative_to(task / "solution")) and (CANARY.search(text) or GUID.search(text)):
            r.err("scrub", f"{where}: canary / GUID-shaped string (ship check 99)")
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
        r.warn("ruff", "ruff not on PATH — install it (py -3 -m pip install ruff)")
    typos = shutil.which("typos")
    if typos:
        proc = subprocess.run([typos, str(task)], capture_output=True, text=True)
        if proc.returncode != 0:
            r.err("typos", f"typos reported issues:\n{proc.stdout.strip()[:1500]}")


def check_task(task: Path, outer: Path | None) -> Report:
    r = Report()
    rubric = (outer or task) / "rubric.txt"
    check_structure(task, outer, r)
    data = check_toml(task, r)
    check_instruction(task, r)
    check_environment(task, r)
    check_verifier_dockerfile(task, data, r)
    check_test_sh(task, r)
    check_manifest(task, r)
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
        print(f"== tb40_check: {task.name} ==")
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
