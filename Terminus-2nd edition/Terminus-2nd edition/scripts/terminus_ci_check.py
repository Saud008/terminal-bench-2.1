#!/usr/bin/env python3
"""Snorkel / Terminus static CI checks (local Python — no manual harbor required).

Mirrors platform CI Checks Reference blocking + warning checks where possible.
Optionally runs `harbor tasks check` / `stb harbor tasks check` when on PATH.

Usage:
  python3 scripts/terminus_ci_check.py --task-dir tasks/<name>
  python3 scripts/terminus_ci_check.py --task-dir tasks/<name> --pack-gate
  python3 scripts/terminus_ci_check.py --task-dir tasks/<name> --json

Reports: jobs-local/ci-check-last.txt
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_LOCAL = REPO_ROOT / "jobs-local"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path  # noqa: E402

REPORT_PATH = jobs_path("ci-check-last.txt")

MI_B = 1024 * 1024
MAX_CONTEXT_BYTES = 100 * MI_B
MAX_FILE_BYTES = 50 * MI_B

# Import allowlist from the single source of truth used by pack_zip.
from ensure_category_allowed import (  # noqa: E402
    ALLOWED as ALLOWED_CATEGORIES,
    BLOCKED as BLOCKED_CATEGORIES,
    GRANDFATHERED_DEBUGGING_SLUGS,
)

SUGGESTED_CATEGORIES = tuple(sorted(ALLOWED_CATEGORIES))

FORBIDDEN_TASK_ROOT_FILES = frozenset({"rubric.md"})

CANONICAL_DIGESTS = frozenset(
    {
        "01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb",
        "f3a68cf41a855d227d1b0ab832bed9749469ef38cf4f58182fb8c893bc462383",
        "1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac",
        "9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36",
        "25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14",
        "930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c",
        "e76733e94b3a5893e4a141024ef3a583dc10781dc24becebf74f9c9f9a33e3df",
        "3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e",
        "4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d",
        "0d39fcc8335d6d74d5502f6df2d30119ff4790ebbb60b364818d5112d9e3e932",
    }
)

FORBIDDEN_SOLUTION_PATTERNS = [
    (r"\bsbt\b", "G-025: no sbt in solve.sh"),
    (r"mix\s+deps\.get", "G-025: no mix deps.get"),
    (r"mix\s+local\.(hex|rebar)", "G-025: no mix local.hex/rebar"),
    (r"\bnpm\s+install\b", "G-025: no npm install"),
    (r"\bpip\s+install\b", "G-025: no pip install"),
    (r"\bcurl\s+", "G-025: no curl in solve.sh"),
    (r"\bwget\s+", "G-025: no wget in solve.sh"),
    (r"apt-get\s+install", "G-025: no apt-get install"),
    (r"cargo\s+fetch", "G-025: no cargo fetch"),
]

AI_SCAFFOLDING_NAMES = frozenset(
    {
        "claude.md",
        "skills.md",
        "skill.md",
        "agents.md",
        "cursor.md",
        ".cursorrules",
        "copilot-instructions.md",
    }
)

TEST_SH_RUNTIME_INSTALL = re.compile(
    r"(pip\s+install|apt-get\s+install|curl\s+|wget\s+|npm\s+install|uvx?\s+|npx\s+)",
    re.I,
)

FROM_RE = re.compile(r"^FROM\s+(.+)$", re.I | re.M)
DIGEST_RE = re.compile(r"@sha256:([a-f0-9]{64})", re.I)
TBENCH_FROM_RE = re.compile(r"ghcr\.io/laude-institute/t-bench/", re.I)
ECR_FROM_PREFIX = "public.ecr.aws/docker/library/"
WORKDIR_RE = re.compile(r"^WORKDIR\s+/app\b", re.I | re.M)


@dataclass
class Check:
    id: str
    severity: str  # block | warn | info
    passed: bool
    message: str
    fix: str = ""


def resolve_task_dir(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def locate_task_dir(name_or_path: str) -> Path | None:
    p = resolve_task_dir(name_or_path)
    if p.is_dir() and (p / "task.toml").is_file():
        return p
    for base in ("tasks", "pending"):
        cand = REPO_ROOT / base / name_or_path.strip("/")
        if cand.is_dir() and (cand / "task.toml").is_file():
            return cand
    return None


def is_milestone(task_dir: Path) -> bool:
    return (task_dir / "steps").is_dir()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def check_structure(task_dir: Path) -> list[Check]:
    out: list[Check] = []
    ms = is_milestone(task_dir)
    if ms:
        required = ["task.toml", "environment/Dockerfile", "steps"]
    else:
        required = [
            "instruction.md",
            "task.toml",
            "environment/Dockerfile",
            "tests/test.sh",
            "tests/test_outputs.py",
            "solution/solve.sh",
        ]
    missing = [r for r in required if not (task_dir / r).exists()]
    present = [r for r in required if (task_dir / r).exists()]
    out.append(
        Check(
            "validate_task_structure",
            "block",
            not missing,
            "OK" if not missing else f"Missing: {', '.join(missing)}",
            "Add required files per Terminus task layout",
        )
    )
    out.append(
        Check(
            "task_files_present",
            "block",
            not missing,
            f"Present ({len(present)}/{len(required)}): {', '.join(present)}"
            if not missing
            else f"Missing files: {', '.join(missing)}",
            "See Task Components — non-milestone or milestone layout",
        )
    )
    return out


def check_task_files(task_dir: Path) -> list[Check]:
    """Forbidden paths, milestone layout, environment hygiene, codebase_size hint."""
    out: list[Check] = []
    ms = is_milestone(task_dir)

    forbidden_root = [n for n in FORBIDDEN_TASK_ROOT_FILES if (task_dir / n).is_file()]
    out.append(
        Check(
            "forbidden_task_root_files",
            "block",
            not forbidden_root,
            "OK — no rubric.md at task root"
            if not forbidden_root
            else f"Remove forbidden root file(s): {', '.join(forbidden_root)}",
            "Do not ship rubric.md in task folder or zip (repo policy)",
        )
    )

    env = task_dir / "environment"
    env_bad: list[str] = []
    if env.is_dir():
        for name in ("tests", "solution", "test_outputs.py", "solve.sh"):
            p = env / name
            if p.exists():
                env_bad.append(f"environment/{name}")
        for f in env.rglob("*"):
            if f.is_file() and f.name.lower() in AI_SCAFFOLDING_NAMES:
                env_bad.append(str(f.relative_to(task_dir)))

    out.append(
        Check(
            "environment_file_hygiene",
            "block",
            not env_bad,
            "OK — no tests/solution/AI scaffolding in environment/"
            if not env_bad
            else f"Remove from environment/: {', '.join(env_bad[:6])}",
            "Keep tests/ and solution/ outside environment/; no CLAUDE.md etc.",
        )
    )

    if ms:
        toml = read_text(task_dir / "task.toml")
        nm = re.search(r"number_of_milestones\s*=\s*(\d+)", toml)
        expected = int(nm.group(1)) if nm else 0
        steps = task_dir / "steps"
        milestones = sorted(
            d.name
            for d in steps.iterdir()
            if d.is_dir() and re.match(r"milestone_\d+$", d.name)
        ) if steps.is_dir() else []
        ms_missing: list[str] = []
        for mname in milestones:
            base = steps / mname
            for rel in ("instruction.md", "tests/test.sh", "solution/solve.sh"):
                if not (base / rel).exists():
                    ms_missing.append(f"{mname}/{rel}")
            py = list((base / "tests").glob("test_m*.py")) if (base / "tests").is_dir() else []
            if not py:
                ms_missing.append(f"{mname}/tests/test_mN.py")

        count_ok = expected > 0 and len(milestones) == expected
        layout_ok = not ms_missing and count_ok
        out.append(
            Check(
                "milestone_files",
                "block",
                layout_ok,
                f"OK — {len(milestones)} milestone(s), layout complete"
                if layout_ok
                else (
                    f"number_of_milestones={expected}, found {len(milestones)}; "
                    f"gaps: {ms_missing[:5]}"
                ),
                "Each steps/milestone_N/ needs instruction.md, tests/, solution/",
            )
        )
    else:
        if (task_dir / "steps").is_dir():
            out.append(
                Check(
                    "non_milestone_root_layout",
                    "block",
                    False,
                    "Non-milestone task has steps/ — use root instruction.md + tests/",
                    "Remove steps/ or convert to milestone task.toml",
                )
            )

    meaningful = 0
    if env.is_dir():
        for f in env.rglob("*"):
            if not f.is_file():
                continue
            rel = str(f.relative_to(env))
            if any(
                skip in rel
                for skip in (".pytest_cache", "__pycache__", ".git", "node_modules", ".ruff_cache")
            ):
                continue
            if f.name in (".dockerignore",):
                continue
            meaningful += 1

    toml = read_text(task_dir / "task.toml")
    size_m = re.search(r'codebase_size\s*=\s*"([^"]+)"', toml)
    size = size_m.group(1) if size_m else ""
    size_ok = True
    msg = f"environment/ meaningful files: {meaningful} (codebase_size={size or '?'})"
    if size == "small" and meaningful < 20:
        size_ok = False
        msg += " — small expects ~20+ meaningful env files"
    elif size == "minimal":
        size_ok = False
        msg += " — new submissions should use small or large, not minimal"
    out.append(
        Check(
            "codebase_size_files",
            "warn" if not size_ok else "block",
            size_ok,
            msg,
            "Add real modules/docs under environment/ or fix codebase_size in task.toml",
        )
    )

    return out


def category_summary(task_dir: Path) -> tuple[str, bool]:
    text = read_text(task_dir / "task.toml")
    cm = re.search(r'category\s*=\s*"([^"]+)"', text)
    cat = cm.group(1) if cm else "(missing)"
    ok = bool(cat) and (
        cat in ALLOWED_CATEGORIES
        or (
            task_dir.name in GRANDFATHERED_DEBUGGING_SLUGS
            and cat in BLOCKED_CATEGORIES
        )
    )
    return cat, ok


def files_summary(task_dir: Path) -> str:
    ms = is_milestone(task_dir)
    if ms:
        required = ["task.toml", "environment/Dockerfile", "steps"]
    else:
        required = [
            "instruction.md",
            "task.toml",
            "environment/Dockerfile",
            "tests/test.sh",
            "tests/test_outputs.py",
            "solution/solve.sh",
        ]
    missing = [r for r in required if not (task_dir / r).exists()]
    if missing:
        return f"MISSING: {', '.join(missing)}"
    env_n = sum(1 for f in (task_dir / "environment").rglob("*") if f.is_file()) if (task_dir / "environment").is_dir() else 0
    return f"all required present · environment/ {env_n} files"


def check_task_toml(task_dir: Path) -> list[Check]:
    out: list[Check] = []
    path = task_dir / "task.toml"
    text = read_text(path)
    if not text:
        return [
            Check("validate_task_fields", "block", False, "task.toml missing or empty", "Add task.toml")
        ]

    ms = is_milestone(task_dir)
    required_keys = [
        "version",
        "author_name",
        "author_email",
        "category",
        "subcategories",
        "difficulty",
        "codebase_size",
        "number_of_milestones",
        "languages",
        "tags",
        "expert_time_estimate_min",
        "junior_time_estimate_min",
        "allow_internet",
    ]
    missing = [k for k in required_keys if k not in text]
    if not ms:
        for k in ("timeout_sec",):
            if "[agent]" not in text or "[verifier]" not in text:
                missing.append("[agent]/[verifier] blocks")

    out.append(
        Check(
            "validate_task_fields",
            "block",
            not missing,
            "OK" if not missing else f"task.toml missing fields/sections: {missing[:8]}",
            "Complete [metadata], [agent], [verifier], [environment] per creation-rules",
        )
    )

    m = re.search(r"subcategories\s*=\s*\[\s*\]", text)
    out.append(
        Check(
            "subcategories_empty",
            "block",
            bool(m),
            "subcategories = []" if m else "subcategories must be []",
            "Set subcategories = [] in task.toml",
        )
    )

    cm = re.search(r'category\s*=\s*"([^"]+)"', text)
    cat = cm.group(1) if cm else ""
    cat_ok = bool(cat) and (
        cat in ALLOWED_CATEGORIES
        or (
            task_dir.name in GRANDFATHERED_DEBUGGING_SLUGS
            and cat in BLOCKED_CATEGORIES
        )
    )
    out.append(
        Check(
            "category_allowed",
            "block",
            cat_ok,
            f'category = "{cat}"' if cat else "category missing",
            "Use data-administration / machine-learning / games only "
            "(not debugging, software-engineering, data-processing, security, "
            "system-administration, build-and-dependency-management, …)",
        )
    )

    if re.search(r"allow_internet\s*=\s*false", text):
        out.append(Check("allow_internet", "block", True, "allow_internet = false", ""))
    else:
        out.append(
            Check(
                "allow_internet",
                "block",
                False,
                "allow_internet must be false unless task needs live network",
                "Set [environment] allow_internet = false",
            )
        )

    if not ms and "workdir" in text and 'workdir = "/app"' not in text:
        out.append(
            Check(
                "workdir_app",
                "warn",
                False,
                'Prefer workdir = "/app" in [environment]',
                'Add workdir = "/app"',
            )
        )

    return out


def check_instruction(task_dir: Path) -> list[Check]:
    out: list[Check] = []
    if is_milestone(task_dir):
        return out
    path = task_dir / "instruction.md"
    text = read_text(path)
    if not text:
        return out

    has_backticks = "`" in text
    out.append(
        Check(
            "instruction_no_backticks",
            "block",
            not has_backticks,
            "instruction.md has backticks" if has_backticks else "OK",
            "Use prose paths without backticks (instruction-prose-style.mdc)",
        )
    )

    rel_bad = re.findall(
        r"(?<![/\w])(?:config|src|docs|output)/[a-zA-Z0-9_./-]+",
        text,
    )
    abs_ok = "/app/" in text or "/opt/" in text or "/output/" in text
    rel_only = rel_bad and not abs_ok
    out.append(
        Check(
            "check_task_absolute_path",
            "block",
            not rel_only,
            "Use absolute paths like /app/..." if rel_only else "OK (absolute paths present)",
            "Rewrite relative paths to /app/... in instruction.md",
        )
    )
    return out


def parse_dockerfile(task_dir: Path) -> tuple[str, list[str]]:
    df = task_dir / "environment" / "Dockerfile"
    text = read_text(df)
    from_lines = FROM_RE.findall(text)
    return text, from_lines


def check_dockerfile(task_dir: Path) -> list[Check]:
    out: list[Check] = []
    df_path = task_dir / "environment" / "Dockerfile"
    if not df_path.is_file():
        return [Check("check_pinned_images", "block", False, "No Dockerfile", "Add environment/Dockerfile")]

    text, from_lines = parse_dockerfile(task_dir)

    unpinned = [
        ln
        for ln in from_lines
        if not DIGEST_RE.search(ln) and not TBENCH_FROM_RE.search(ln)
    ]
    out.append(
        Check(
            "check_pinned_images",
            "block",
            not unpinned,
            "All FROM digest-pinned" if not unpinned else f"Unpinned FROM: {unpinned[:2]}",
            "Add @sha256:<digest> to every FROM line",
        )
    )

    non_ecr = [
        ln
        for ln in from_lines
        if ECR_FROM_PREFIX not in ln and not TBENCH_FROM_RE.search(ln)
    ]
    out.append(
        Check(
            "check_ecr_canonical_from",
            "block",
            not non_ecr,
            "All FROM use Snorkel ECR (every stage)"
            if not non_ecr
            else f"Non-ECR FROM ({len(non_ecr)}): {non_ecr[0][:72]}…",
            "Run: python3 scripts/migrate_dockerfile_canonical_ecr.py --ensure --task-dir <task>; "
            "copy exact FROM from canonical-base-image-gate.mdc (builder + runtime)",
        )
    )

    if from_lines:
        final_from = from_lines[-1]
        digest_m = DIGEST_RE.search(final_from)
        digest = digest_m.group(1).lower() if digest_m else ""
        canonical = digest in CANONICAL_DIGESTS or bool(TBENCH_FROM_RE.search(final_from))
        has_justify = bool(
            re.search(r"(?i)(non-canonical|justification|custom base|elixir|zig|crystal)", text)
        )
        out.append(
            Check(
                "check_sanctioned_base_images",
                "block",
                canonical or has_justify,
                f"Final FROM digest {digest[:12]}…" + (" canonical" if canonical else " (needs justification if non-canonical)"),
                "Use Snorkel ECR canonical FROM (canonical-base-image-gate.mdc) or add credible Dockerfile comment",
            )
        )

    total = 0
    big_files: list[str] = []
    env = task_dir / "environment"
    if env.is_dir():
        for f in env.rglob("*"):
            if f.is_file():
                try:
                    sz = f.stat().st_size
                except OSError:
                    continue
                total += sz
                if sz > MAX_FILE_BYTES:
                    big_files.append(f"{f.relative_to(env)} ({sz // MI_B} MiB)")

    out.append(
        Check(
            "check_build_context_size",
            "block",
            total <= MAX_CONTEXT_BYTES and not big_files,
            f"environment/ {total // MI_B} MiB" + (f"; oversized: {big_files[:3]}" if big_files else ""),
            "Keep environment/ ≤ 100 MiB; no file > 50 MiB",
        )
    )

    copy_bad = re.search(
        r"COPY\s+.*\b(tests|solution)/",
        text,
        re.I,
    )
    out.append(
        Check(
            "tests_or_solution_in_image",
            "block",
            not copy_bad,
            "No tests/solution COPY in Dockerfile" if not copy_bad else str(copy_bad.group(0)),
            "Remove COPY tests/ or solution/ from Dockerfile",
        )
    )

    ref_bad = re.search(r"(solve\.sh|test_outputs\.py|tests/test\.sh)", text, re.I)
    out.append(
        Check(
            "check_dockerfile_references",
            "block",
            not ref_bad,
            "OK" if not ref_bad else f"Forbidden reference: {ref_bad.group(0)}",
            "Do not reference solution/tests paths in Dockerfile",
        )
    )

    if not WORKDIR_RE.search(text):
        out.append(
            Check(
                "dockerfile_workdir",
                "block",
                False,
                "Missing WORKDIR /app",
                "Add WORKDIR /app to Dockerfile",
            )
        )

    if not re.search(r"\btmux\b", text, re.I):
        out.append(Check("tmux_installed", "block", False, "tmux not in Dockerfile", "Install tmux in Dockerfile"))
    if not re.search(r"\basciinema\b", text, re.I):
        out.append(
            Check("asciinema_installed", "block", False, "asciinema not in Dockerfile", "Install asciinema in Dockerfile")
        )

    if not (task_dir / "environment" / ".dockerignore").is_file():
        out.append(
            Check(
                "check_dockerignore",
                "warn",
                False,
                "Missing environment/.dockerignore",
                "Add .dockerignore excluding solution/, tests/, caches",
            )
        )

    if re.search(r"chmod\s+-R|chown\s+-R", text, re.I):
        out.append(
            Check(
                "check_recursive_permissions",
                "warn",
                False,
                "Broad chmod -R / chown -R in Dockerfile",
                "Use COPY --chmod / --chown on specific paths",
            )
        )

    if re.search(r"<<['\"]?EOF", text):
        out.append(
            Check(
                "check_heredoc_usage",
                "warn",
                False,
                "Heredoc embeds source in Dockerfile",
                "COPY source files instead of heredocs",
            )
        )

    if re.search(r"COPY\s+\.\s+/app", text, re.I):
        out.append(
            Check(
                "check_layer_volatility",
                "warn",
                False,
                "COPY . /app without narrow context",
                "Prefer COPY src/ manifests; strict .dockerignore",
            )
        )

    apt_runs = len(re.findall(r"apt-get\s+update", text, re.I))
    if apt_runs > 2:
        out.append(
            Check(
                "check_apt_usage",
                "warn",
                False,
                f"Multiple apt-get update layers ({apt_runs})",
                "Consolidate apt into one RUN transaction",
            )
        )

    for name in AI_SCAFFOLDING_NAMES:
        for hit in (task_dir / "environment").rglob(name):
            out.append(
                Check(
                    "environment_no_ai_scaffolding",
                    "block",
                    False,
                    f"AI scaffolding file: {hit.relative_to(task_dir)}",
                    "Remove or rename to task-specific docs",
                )
            )
            break

    return out


def _validate_test_sh_content(text: str, label: str) -> list[Check]:
    out: list[Check] = []
    if not text:
        return [Check("check_test_sh", "block", False, f"{label} missing", "Add test.sh")]

    reward_end = bool(
        re.search(
            r"if\s+\[\s*\$\?\s*-eq\s+0\s*\]\s*;\s*then\s*\n\s*echo\s+1\s*>\s*/logs/verifier/reward\.txt",
            text,
        )
        or re.search(
            r"rc=\$\?\s*\nif\s+\[\s*\"\$rc\"\s*-eq\s+0\s*\]",
            text,
        )
    )
    out.append(
        Check(
            "check_test_sh",
            "block",
            reward_end and "/logs/verifier/reward.txt" in text,
            f"{label}: reward.txt block present"
            if reward_end
            else f"{label}: Missing Harbor reward block at end of test.sh",
            "End test.sh with if [ $? -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0; fi",
        )
    )

    if TEST_SH_RUNTIME_INSTALL.search(text):
        m = TEST_SH_RUNTIME_INSTALL.search(text)
        out.append(
            Check(
                "check_offline_tests",
                "block",
                False,
                f"Runtime install/download in {label}: {m.group(0) if m else '?'}",
                "Install verifier deps in Dockerfile only",
            )
        )
    else:
        out.append(Check("check_offline_tests", "block", True, f"{label}: no runtime installs", ""))

    if "echo 0 > /logs/verifier/reward.txt" not in text and "echo 0>/logs/verifier/reward.txt" not in text.replace(" ", ""):
        out.append(
            Check(
                "test_sh_bootstrap_reward",
                "warn",
                False,
                f"{label}: seed reward 0 before pytest not found",
                "Bootstrap /logs/verifier and prewrite 0 before guards",
            )
        )

    return out


def check_test_sh(task_dir: Path) -> list[Check]:
    if is_milestone(task_dir):
        steps = task_dir / "steps"
        milestones = sorted(
            d for d in steps.iterdir() if d.is_dir() and re.match(r"milestone_\d+$", d.name)
        )
        if not milestones:
            return [
                Check(
                    "check_test_sh",
                    "block",
                    False,
                    "Milestone task has no steps/milestone_N/ folders",
                    "Add milestone folders with tests/test.sh each",
                )
            ]
        out: list[Check] = []
        for mdir in milestones:
            rel = f"steps/{mdir.name}/tests/test.sh"
            out.extend(_validate_test_sh_content(read_text(mdir / "tests" / "test.sh"), rel))
        return out

    return _validate_test_sh_content(read_text(task_dir / "tests" / "test.sh"), "tests/test.sh")


def check_solution(task_dir: Path) -> list[Check]:
    out: list[Check] = []
    for rel in ("solution/solve.sh",):
        path = task_dir / rel
        if not path.is_file():
            continue
        text = read_text(path)
        for pat, msg in FORBIDDEN_SOLUTION_PATTERNS:
            if re.search(pat, text, re.I):
                out.append(
                    Check("G-025_oracle_offline", "block", False, f"{rel}: {msg}", "Offline oracle per oracleFix.md")
                )
                break
        else:
            out.append(Check("G-025_oracle_offline", "block", True, f"{rel} no network/toolchain fetch", ""))
    return out


def check_g026_zip_readiness(task_dir: Path) -> list[Check]:
    if is_milestone(task_dir):
        return []
    ok = (task_dir / "tests" / "test_outputs.py").is_file()
    return [
        Check(
            "G-026_test_outputs_py",
            "block",
            ok,
            "tests/test_outputs.py present" if ok else "Missing tests/test_outputs.py (G-026)",
            "Add tests/test_outputs.py for non-milestone tasks",
        )
    ]


def run_ruff(task_dir: Path) -> list[Check]:
    ruff = shutil.which("ruff")
    if not ruff:
        return [Check("ruff", "info", True, "skipped — ruff not on PATH", "Install ruff or run in CI")]

    targets: list[str] = []
    if is_milestone(task_dir):
        steps = task_dir / "steps"
        for mdir in sorted(steps.iterdir()) if steps.is_dir() else []:
            tests = mdir / "tests"
            if tests.is_dir():
                targets.append(str(tests))
    else:
        tests = task_dir / "tests"
        if tests.is_dir():
            targets.append(str(tests))
    if not targets:
        return []

    proc = subprocess.run(
        [ruff, "check", *targets],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return [
        Check(
            "ruff",
            "block",
            proc.returncode == 0,
            "ruff clean" if proc.returncode == 0 else out.strip()[:500],
            "ruff check --fix tests/",
        )
    ]


def run_harbor(task_dir: Path) -> list[Check]:
    try:
        rel = task_dir.relative_to(REPO_ROOT)
    except ValueError:
        rel = task_dir
    candidates = [
        ["stb", "harbor", "tasks", "check", str(rel), "-m", "openai/@openai/gpt-5.5"],
        ["harbor", "tasks", "check", str(rel), "-m", "openai/@openai/gpt-5.5"],
    ]
    for cmd in candidates:
        if not shutil.which(cmd[0]):
            continue
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=300,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            return [Check("harbor_tasks_check", "info", False, str(exc), "")]
        out = (proc.stdout or "") + (proc.stderr or "")
        return [
            Check(
                "harbor_tasks_check",
                "block" if proc.returncode != 0 else "info",
                proc.returncode == 0,
                out.strip()[:800] if out else f"exit {proc.returncode}",
                "Fix failures from harbor tasks check",
            )
        ]
    return [
        Check(
            "harbor_tasks_check",
            "info",
            True,
            "skipped — stb/harbor not on PATH (local Python checks still ran)",
            "",
        )
    ]


def run_all_checks(
    task_dir: Path, *, harbor_llmaj: bool = False, ruff: bool = True
) -> list[Check]:
    checks: list[Check] = []
    checks.extend(check_structure(task_dir))
    checks.extend(check_task_files(task_dir))
    checks.extend(check_task_toml(task_dir))
    checks.extend(check_instruction(task_dir))
    checks.extend(check_dockerfile(task_dir))
    checks.extend(check_test_sh(task_dir))
    checks.extend(check_solution(task_dir))
    checks.extend(check_g026_zip_readiness(task_dir))
    if ruff:
        checks.extend(run_ruff(task_dir))
    # Local instruction/test quality heuristics (no API keys). Harbor GPT LLMaJ opt-in only.
    try:
        from terminus_llmaj_check import run_all_llmaj

        checks.extend(run_all_llmaj(task_dir, harbor=harbor_llmaj))
    except ImportError:
        pass
    return checks


def format_report(task_dir: Path, checks: list[Check]) -> str:
    blocks = [c for c in checks if c.severity == "block" and not c.passed]
    warns = [c for c in checks if c.severity == "warn" and not c.passed]
    passed = sum(1 for c in checks if c.passed)

    cat, cat_ok = category_summary(task_dir)
    fsum = files_summary(task_dir)
    llmaj_ids = (
        "behavior_in_task_description",
        "behavior_in_tests",
        "informative_test_docstrings",
        "anti_cheating_measures",
        "structured_data_schema",
        "hardcoded_solution",
        "file_reference_mentioned",
    )
    llmaj_checks = [c for c in checks if c.id in llmaj_ids]
    llmaj_pass = sum(1 for c in llmaj_checks if c.passed)

    lines = [
        f"# CI preflight — {task_dir.name}",
        f"Path: {task_dir}",
        "",
        f"Summary: {passed}/{len(checks)} passed · {len(blocks)} blocking · {len(warns)} warnings",
        "",
        "## Category",
        f"- task.toml category: **{cat}** — {'PASS' if cat_ok else 'BLOCK'}",
        f"- Allowed examples: {', '.join(SUGGESTED_CATEGORIES)}",
        f"- Blocked: {', '.join(sorted(BLOCKED_CATEGORIES))}",
        "",
        "## Files",
        f"- Layout: {fsum}",
        "",
        f"## Quality heuristics ({llmaj_pass}/{len(llmaj_ids)} local)",
    ]
    for lid in llmaj_ids:
        hit = next((c for c in checks if c.id == lid), None)
        if hit:
            mark = "PASS" if hit.passed else hit.severity.upper()
            lines.append(f"- [{mark}] {lid}")
    lines.extend(
        [
            "",
            "Full LLMaJ: jobs-local/llmaj-check-last.txt",
            "",
        ]
    )
    if blocks:
        lines.append("## BLOCKING")
        for c in blocks:
            lines.append(f"- **{c.id}**: {c.message}")
            if c.fix:
                lines.append(f"  - Fix: {c.fix}")
        lines.append("")
    if warns:
        lines.append("## WARNINGS")
        for c in warns:
            lines.append(f"- **{c.id}**: {c.message}")
        lines.append("")
    lines.append("## ALL")
    for c in checks:
        mark = "PASS" if c.passed else c.severity.upper()
        lines.append(f"- [{mark}] {c.id}: {c.message[:120]}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, help="tasks/<name> or pending/<name>")
    parser.add_argument("--pack-gate", action="store_true", help="Exit 1 on any blocking failure")
    parser.add_argument(
        "--harbor-llmaj",
        action="store_true",
        help="Run harbor GPT LLMaJ (needs stb keys) — off by default for pack",
    )
    parser.add_argument(
        "--no-harbor",
        action="store_true",
        help="Deprecated alias (harbor LLMaJ already off by default)",
    )
    parser.add_argument("--no-ruff", action="store_true", help="Skip ruff")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--quiet", action="store_true", help="Only print on failure or --json")
    args = parser.parse_args()

    task_dir = locate_task_dir(args.task_dir)
    if not task_dir:
        print(f"ERROR: task not found: {args.task_dir}", file=sys.stderr)
        return 1

    checks = run_all_checks(
        task_dir,
        harbor_llmaj=args.harbor_llmaj and not args.no_harbor,
        ruff=not args.no_ruff,
    )
    report = format_report(task_dir, checks)

    JOBS_LOCAL.mkdir(parents=True, exist_ok=True)
    report_out = jobs_path("ci-check-last.txt", mkdir=True)
    report_out.write_text(report, encoding="utf-8")

    blocks = [c for c in checks if c.severity == "block" and not c.passed]
    ok = not blocks

    if args.json:
        print(
            json.dumps(
                {
                    "task": task_dir.name,
                    "path": str(task_dir),
                    "ok": ok,
                    "blocking": [asdict(c) for c in blocks],
                    "checks": [asdict(c) for c in checks],
                    "report_path": str(report_out),
                },
                indent=2,
            )
        )
    elif not args.quiet or not ok:
        print(report)
        print(f"\nReport: {report_out}")

    if args.pack_gate and not ok:
        print(f"CI check FAIL — {len(blocks)} blocking issue(s)", file=sys.stderr)
        return 1

    return 0 if ok else (1 if args.pack_gate else 0)


if __name__ == "__main__":
    sys.exit(main())
