#!/usr/bin/env python3
"""Scaffold a TB 2.1 task in the pool delivery layout.

Creates <slug>/<slug>/ from tb21/skeleton/task, <slug>/rubric.txt from the
skeleton rubric, and empty oracle-nop-evidence/ and trajectories/ folders.

Usage:
    py -3 tb21/new_task.py <kebab-case-slug> [--dest <parent-dir>]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SKELETON = Path(__file__).resolve().parent / "skeleton"
EVIDENCE_RUNS = ("oracle-1", "oracle-2", "oracle-3", "nop-1", "nop-2")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    parser.add_argument("--dest", default=".", help="parent directory (default: current directory)")
    args = parser.parse_args()

    slug = args.slug
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)+", slug):
        print(f"slug '{slug}' must be descriptive kebab-case (e.g. ledger-rollup-drift-repair)")
        return 2
    if re.search(r"(^|-)(hardened|fixed|patched|final|draft|v\d+|round\d*|copy|tmp|wip|test|task\d*)(-|$)", slug):
        print(f"slug '{slug}' is generic or reveals process history")
        return 2

    outer = Path(args.dest).resolve() / slug
    if outer.exists():
        print(f"{outer} already exists")
        return 1

    shutil.copytree(SKELETON / "task", outer / slug)
    shutil.copy2(SKELETON / "rubric.txt", outer / "rubric.txt")
    for run in EVIDENCE_RUNS:
        (outer / "oracle-nop-evidence" / run).mkdir(parents=True)
    (outer / "trajectories").mkdir()

    print(f"created {outer}")
    print(f"  task:     {outer / slug}")
    print(f"  rubric:   {outer / 'rubric.txt'}")
    print(f"  next:     py -3 tb21/tb21_check.py {outer}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
