#!/usr/bin/env python3
"""Harbor edition_2 category gate for this project.

Hard task.toml blocklist: debugging, software-engineering
Classifier-blocked when predicted (evidence 2026-07-27): debugging,
software-engineering, data-processing, security
Also invalid schema: data-administration

Prefer: games | machine-learning | system-administration
(scientific-computing / build-and-dependency-management are sometimes classifier-blocked)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

HARBOR_SCHEMA = frozenset(
    {
        "build-and-dependency-management",
        "data-processing",
        "debugging",
        "games",
        "machine-learning",
        "scientific-computing",
        "security",
        "software-engineering",
        "system-administration",
    }
)

PROJECT_BLOCKED = frozenset({"debugging", "software-engineering"})
# Alias used by terminus_ci_check / pack preflight
BLOCKED = PROJECT_BLOCKED

CLASSIFIER_RISKY = frozenset(
    {
        "debugging",
        "software-engineering",
        "data-processing",
        "security",
        "data-administration",
    }
)

# Preferred safe lanes for Rust CLI ledger/planner shapes.
PREFERRED = frozenset({"games", "machine-learning", "system-administration"})

ALLOWED = HARBOR_SCHEMA - PROJECT_BLOCKED

REMAP_HINTS: dict[str, str] = {
    "data-administration": "games",
    "debugging": "games",
    "software-engineering": "games",
    "data-processing": "games",
    "security": "games",
    "scientific-computing": "games",
    "build-and-dependency-management": "system-administration",
    "system-configuration-and-setup": "system-administration",
    "cloud-devops": "system-administration",
}

GRANDFATHERED_DEBUGGING_SLUGS = frozenset()
CATEGORY_RE = re.compile(r'^category\s*=\s*"([^"]+)"\s*$', re.MULTILINE)
RULE = ".cursor/rules/shared/task-toml-category-gate.mdc"


def resolve_task_dir(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def check_task_toml(path: Path) -> tuple[bool, str | None]:
    if not path.is_file():
        return False, f"missing {path}"

    text = path.read_text(encoding="utf-8")
    m = CATEGORY_RE.search(text)
    if not m:
        return False, f'no category = "..." in {path}'

    category = m.group(1)
    slug = path.parent.name
    if slug in GRANDFATHERED_DEBUGGING_SLUGS and category in PROJECT_BLOCKED:
        return True, None
    if category not in HARBOR_SCHEMA:
        hint = REMAP_HINTS.get(category, "games")
        return False, (
            f'category = "{category}" is not in Harbor edition_2 schema '
            f"(must be one of: {', '.join(sorted(HARBOR_SCHEMA))}); "
            f"suggested remap: {hint}; see {RULE}"
        )
    if category in PROJECT_BLOCKED or category in CLASSIFIER_RISKY:
        hint = REMAP_HINTS.get(category, "games")
        return False, (
            f'category = "{category}" is blocked/risky for this project; '
            f"prefer one of: {', '.join(sorted(PREFERRED))}; "
            f"suggested remap: {hint}; reframe instruction.md; see {RULE}"
        )
    return True, None


def suggest_remap(path: Path) -> tuple[str | None, str | None]:
    if not path.is_file():
        return None, f"missing {path}"
    text = path.read_text(encoding="utf-8")
    m = CATEGORY_RE.search(text)
    if not m:
        return None, f'no category = "..." in {path}'
    category = m.group(1)
    if category in ALLOWED and category not in CLASSIFIER_RISKY:
        return category, category
    return category, REMAP_HINTS.get(category, "games")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=str)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--ensure", action="store_true")
    parser.add_argument("--suggest", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if not args.task_dir:
        parser.error("--task-dir is required")

    task_toml = resolve_task_dir(args.task_dir) / "task.toml"
    if args.suggest:
        current, suggested = suggest_remap(task_toml)
        if current is None:
            print(f"ERROR: {suggested}", file=sys.stderr)
            return 1
        print(f"{current} -> {suggested}")
        return 0 if current in ALLOWED and current not in CLASSIFIER_RISKY else 1

    ok, err = check_task_toml(task_toml)
    if ok:
        if not args.quiet:
            print("OK category allowed")
        return 0

    print(f"ERROR: {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
