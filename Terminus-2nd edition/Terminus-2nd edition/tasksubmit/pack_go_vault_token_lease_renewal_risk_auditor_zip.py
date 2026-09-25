#!/usr/bin/env python3
"""Pack go-vault-token-lease-renewal-risk-auditor submission zip with POSIX paths."""

from __future__ import annotations

import zipfile
from pathlib import Path

TASK = (
    Path(__file__).resolve().parent.parent
    / "tasks"
    / "go-vault-token-lease-renewal-risk-auditor"
)
OUT = (
    Path(__file__).resolve().parent
    / "go-vault-token-lease-renewal-risk-auditor.zip"
)
SKIP_DIRS = {".ruff_cache", "__pycache__", ".git", ".pytest_cache", "target", "output", "jobs"}
SKIP_FILES = {"rubric.md"}

if OUT.exists():
    OUT.unlink()

with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(TASK.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        if path.is_file():
            zf.write(path, path.relative_to(TASK).as_posix())

with zipfile.ZipFile(OUT) as zf:
    names = zf.namelist()
    required = [
        "instruction.md",
        "task.toml",
        "environment/Dockerfile",
        "tests/test.sh",
        "tests/test_outputs.py",
        "solution/solve.sh",
    ]
    missing = [r for r in required if r not in names]
    bad = [n for n in names if "\\" in n]
    top = sorted({n.split("/")[0] for n in names})
    print(f"Wrote {OUT}")
    print(f"bytes: {OUT.stat().st_size}")
    print(f"total files: {len(names)}")
    print(f"top-level entries: {top}")
    print(f"missing required: {missing}")
    print(f"backslashes: {bad}")
    if missing or bad:
        raise SystemExit(1)
