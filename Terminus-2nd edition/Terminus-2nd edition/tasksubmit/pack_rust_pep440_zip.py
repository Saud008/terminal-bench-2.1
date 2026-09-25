#!/usr/bin/env python3
"""Pack rust-pep440-wheel-resolution-explainer submission zip with POSIX paths."""

from __future__ import annotations

import zipfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent / "tasks" / "rust-pep440-wheel-resolution-explainer"
OUT = Path(__file__).resolve().parent / "rust-pep440-wheel-resolution-explainer.zip"
SKIP_DIRS = {".ruff_cache", "__pycache__", ".git", "target"}

if OUT.exists():
    OUT.unlink()

with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(TASK.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            zf.write(path, path.relative_to(TASK).as_posix())

with zipfile.ZipFile(OUT) as zf:
    names = zf.namelist()
    roots = sorted({n.split("/")[0] for n in names})
    print(f"Wrote {OUT}")
    print(f"roots: {roots}")
    print(f"backslashes: {[n for n in names if chr(92) in n]}")
    print(f"environment/Dockerfile: {'environment/Dockerfile' in names}")
    print(f"environment/Cargo.lock: {'environment/Cargo.lock' in names}")
    print(f"tests/test.sh: {'tests/test.sh' in names}")
    print(f"total files: {len(names)}")
