#!/usr/bin/env python3
"""Pack ldap-changelog-shadow-sync-cli submission zip with POSIX paths for Linux CI."""

from __future__ import annotations

import zipfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent / "tasks" / "ldap-changelog-shadow-sync-cli"
OUT = Path(__file__).resolve().parent / "ldap-changelog-shadow-sync-cli.zip"
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "output", "state"}

if OUT.exists():
    OUT.unlink()

with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(TASK.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            arc = path.relative_to(TASK).as_posix()
            zf.write(path, arc)

with zipfile.ZipFile(OUT) as zf:
    names = zf.namelist()
    required = [
        "instruction.md",
        "task.toml",
        "environment/Dockerfile",
        "environment/.dockerignore",
        "tests/test.sh",
        "tests/test_outputs.py",
        "solution/solve.sh",
    ]
    missing = [r for r in required if r not in names]
    bad = [n for n in names if chr(92) in n]
    roots = sorted({n.split("/")[0] for n in names if n.strip()})
    nested = [n for n in names if n.startswith("ldap-changelog-shadow-sync-cli/")]
    print(f"Wrote {OUT}")
    print(f"bytes: {OUT.stat().st_size}")
    print(f"total files: {len(names)}")
    print(f"top-level roots: {roots}")
    print(f"missing required: {missing}")
    print(f"backslashes: {bad}")
    print(f"nested wrapper entries: {len(nested)}")
    if missing or bad or nested:
        raise SystemExit(1)
