#!/usr/bin/env python3
"""Canonical paths for jobs-local artifacts (subfolders) + repo rubrics/.

Writers use subfolders; readers fall back to flat jobs-local/ for legacy files.

  python3 scripts/jobs_local_paths.py --resolve harbor-verify-foo.json
  python3 scripts/jobs_local_paths.py --migrate
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_LOCAL = REPO_ROOT / "jobs-local"
RUBRICS_DIR = REPO_ROOT / "rubrics"


def rubric_path(slug: str) -> Path:
    """Platform upload rubric — never inside tasks/ or zips."""
    return RUBRICS_DIR / f"{slug}.md"


def _subdir_for(basename: str) -> str:
    """Map a jobs-local basename to a subfolder name."""
    if basename.startswith("post-create-audit"):
        return "audit"
    if basename.startswith("anti-spam"):
        return "anti-spam"
    if basename in (
        "unacceptable-class-gate-last.json",
        "unacceptable-class-gate-last.txt",
        "ci-check-last.txt",
        "llmaj-check-last.txt",
        "accepted-feedback-gates-last.json",
        "reviewer-feedback-gate-last.json",
        "trivial-shape-last.txt",
    ):
        return "gates"
    if basename.startswith("harbor-"):
        return "harbor"
    if basename.startswith("agent-smoke-") or basename.startswith("trivial-easy-context-") or basename.startswith(
        "reviewer-feedback-context-"
    ):
        return "calibration"
    if basename.startswith("auto-probes-"):
        return "probes"
    if basename.startswith("first-submit"):
        return "first-submit"
    if basename.startswith("create-finish") or basename.startswith("finish-bg-"):
        return "finish"
    if basename.startswith("trivial-easy-pipeline"):
        return "trivial-easy"
    if basename in (
        "ideas-draft.json",
        "idea-similarity-gate-last.json",
        "anti-spam-ideas-last.json",
    ):
        return "ideas"
    if basename.startswith("anti-spam"):
        return "anti-spam"
    return ""


def jobs_path(basename: str, *, mkdir: bool = False) -> Path:
    """Preferred write path for a jobs-local artifact basename."""
    sub = _subdir_for(basename)
    if sub:
        parent = JOBS_LOCAL / sub
        if mkdir:
            parent.mkdir(parents=True, exist_ok=True)
        return parent / basename
    if mkdir:
        JOBS_LOCAL.mkdir(parents=True, exist_ok=True)
    return JOBS_LOCAL / basename


def resolve_jobs_path(basename: str) -> Path:
    """Read path: subfolder first, then legacy flat jobs-local/."""
    preferred = jobs_path(basename)
    if preferred.is_file():
        return preferred
    legacy = JOBS_LOCAL / basename
    if legacy.is_file():
        return legacy
    return preferred


def migrate_flat_to_subfolders() -> list[str]:
    """Move flat jobs-local/* into subfolders. Returns moved basenames."""
    if not JOBS_LOCAL.is_dir():
        return []
    moved: list[str] = []
    for item in sorted(JOBS_LOCAL.iterdir()):
        if not item.is_file():
            continue
        sub = _subdir_for(item.name)
        if not sub:
            continue
        dest_dir = JOBS_LOCAL / sub
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / item.name
        if dest.exists():
            continue
        shutil.move(str(item), str(dest))
        moved.append(item.name)

    # Legacy platform rubrics in jobs-local → rubrics/
    RUBRICS_DIR.mkdir(parents=True, exist_ok=True)
    for item in JOBS_LOCAL.glob("platform-rubric-*.md"):
        slug = item.name.replace("platform-rubric-", "").replace(".md", "")
        dest = rubric_path(slug)
        if dest.exists():
            continue
        shutil.move(str(item), str(dest))
        moved.append(item.name)
    for item in JOBS_LOCAL.glob("**/platform-rubric-*.md"):
        if item.parent == JOBS_LOCAL:
            continue
        slug = item.name.replace("platform-rubric-", "").replace(".md", "")
        dest = rubric_path(slug)
        if dest.exists():
            continue
        shutil.move(str(item), str(dest))
        moved.append(str(item.relative_to(JOBS_LOCAL)))

    return moved


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolve", metavar="BASENAME", default="")
    parser.add_argument("--write", metavar="BASENAME", default="")
    parser.add_argument("--migrate", action="store_true")
    parser.add_argument("--rubric", metavar="SLUG", default="")
    args = parser.parse_args()

    if args.migrate:
        moved = migrate_flat_to_subfolders()
        print(json.dumps({"moved": moved, "count": len(moved)}, indent=2))
        return 0
    if args.resolve:
        print(resolve_jobs_path(args.resolve))
        return 0
    if args.write:
        print(jobs_path(args.write, mkdir=True))
        return 0
    if args.rubric:
        print(rubric_path(args.rubric))
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
