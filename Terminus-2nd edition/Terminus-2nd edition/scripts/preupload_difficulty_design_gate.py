#!/usr/bin/env python3
"""Design gate — block zip when task *looks* platform-EASY (not just shallow probes).

Checks (first upload only):
  G1  task.toml difficulty must be "hard" (repo default — no medium/easy first uploads)
  G2  platform EASY/TRIVIAL context without post-harden calibration → block
  G3  per-test pass rates in platform context: if ≥75% tests at ≥9/10 → surface-easy

  python3 scripts/preupload_difficulty_design_gate.py --pack-gate --task-dir tasks/<name>

Override (user explicit only): TERMINUS_DIFFICULTY_DESIGN_SKIP=1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import resolve_jobs_path  # noqa: E402

PLATFORM_FILE = REPO_ROOT / "scripts" / "platform_submissions.txt"

HARD_TARGET_FLOOR = 0.20


def _slug(task_dir: Path) -> str:
    return task_dir.resolve().name


def _platform_slugs() -> set[str]:
    if not PLATFORM_FILE.is_file():
        return set()
    out: set[str] = set()
    for line in PLATFORM_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line.split()[0])
    return out


def _read_difficulty(task_dir: Path) -> str:
    path = task_dir / "task.toml"
    if not path.is_file():
        return ""
    m = re.search(r'^\s*difficulty\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip().lower() if m else ""


def _parse_per_test_rates(text: str) -> list[float]:
    """From platform Unit Tests Results lines: 9 passed / 10 runs → 0.9"""
    rates: list[float] = []
    for line in text.splitlines():
        if "passed" not in line.lower() or "runs" not in line.lower():
            continue
        m = re.search(r"(\d+)\s+passed\s*/\s*(\d+)\s+runs", line, re.I)
        if m:
            passed, total = int(m.group(1)), int(m.group(2))
            if total > 0:
                rates.append(passed / total)
    return rates


def _instruction_recipe_score(task_dir: Path) -> int:
    """Higher = more step-by-step recipe in instruction (bad for hardness)."""
    path = task_dir / "instruction.md"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    score = 0
    if re.search(r"\bingest\b", text) and re.search(r"\bexport\b", text):
        score += 1
    if re.search(r"subcommand|then run|must run|first .* then", text):
        score += 1
    if len(text.splitlines()) > 45:
        score += 1
    if text.count("must ") >= 6:
        score += 1
    return score


def _context_path(slug: str) -> Path:
    return resolve_jobs_path(f"trivial-easy-context-{slug}.json")


def _load_platform_context(slug: str) -> dict | None:
    path = _context_path(slug)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _skip_pack_gates(slug: str) -> bool:
    if slug not in _platform_slugs():
        return False
    ctx_path = resolve_jobs_path(f"trivial-easy-context-{slug}.json")
    if not ctx_path.is_file():
        return True
    try:
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    return ctx.get("difficulty") not in ("EASY", "TRIVIAL")


def cmd_pack_gate(args: argparse.Namespace) -> int:
    if os.environ.get("TERMINUS_DIFFICULTY_DESIGN_SKIP") == "1":
        print("SKIP difficulty design gate (TERMINUS_DIFFICULTY_DESIGN_SKIP=1)")
        return 0

    task_dir = Path(args.task_dir).resolve()
    slug = _slug(task_dir)
    if _skip_pack_gates(slug):
        print(f"SKIP difficulty design gate — {slug} on platform, no EASY/TRIVIAL revise context")
        return 0

    failures: list[str] = []

    # G1 — metadata honesty (user wants HARD, not medium uploads)
    diff = _read_difficulty(task_dir)
    if diff not in ("hard",):
        failures.append(
            f'G1 task.toml difficulty={diff!r} — first upload must be difficulty = "hard" '
            "(set hard + Case 6 depth, not medium/easy labels)"
        )

    ctx_path = resolve_jobs_path(f"trivial-easy-context-{slug}.json")
    smoke_path = resolve_jobs_path(f"agent-smoke-{slug}.json")
    ctx: dict | None = None
    if ctx_path.is_file():
        try:
            ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            ctx = None

    smoke: dict | None = None
    if smoke_path.is_file():
        try:
            smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            smoke = None

    post_harden_clear = bool(
        smoke
        and smoke.get("post_harden")
        and float(smoke.get("worst_rate", 1.0)) <= HARD_TARGET_FLOOR
    )

    # G2 — platform EASY/TRIVIAL without post-harden clearance
    if ctx and ctx.get("difficulty") in ("EASY", "TRIVIAL"):
        post_harden = bool(smoke and smoke.get("post_harden"))
        if not post_harden:
            failures.append(
                f"G2 platform label {ctx['difficulty']} on record — "
                "Case 6 structural harden + local smoke, then "
                "preupload_agent_calibration.py --record --post-harden with worst ≤20%"
            )

    # G3 — surface-easy per-test table (e.g. vulkan 22/24 tests at 9–10/10)
    snippet = ""
    if ctx:
        snippet = str(ctx.get("raw_snippet", ""))
    rates = _parse_per_test_rates(snippet)
    if len(rates) >= 8 and not post_harden_clear:
        hot = sum(1 for r in rates if r >= 0.9)
        if hot / len(rates) >= 0.75:
            failures.append(
                f"G3 platform per-test table: {hot}/{len(rates)} tests ≥90% pass — "
                "agents solve in one pass; add hidden-only traps + interaction bugs (Case 6)"
            )

    # G4 — instruction recipe leak (optional warn → fail when combined with G2/G3)
    recipe = _instruction_recipe_score(task_dir)
    if recipe >= 3 and (ctx and ctx.get("difficulty") in ("EASY", "TRIVIAL")):
        failures.append(
            f"G4 instruction reads like a fix recipe (score {recipe}/4) — "
            "shorten instruction.md; move contracts to /app/docs/ only"
        )

    if failures:
        print("FAIL difficulty design gate:", file=sys.stderr)
        for f in failures:
            print(f"  • {f}", file=sys.stderr)
        print("  Policy: shared/no-easy-upload-lock.mdc", file=sys.stderr)
        return 1

    print(f"PASS difficulty design gate — {slug}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--pack-gate", action="store_true")
    args = parser.parse_args()
    if args.pack_gate:
        return cmd_pack_gate(args)
    parser.error("use --pack-gate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
