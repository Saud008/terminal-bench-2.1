#!/usr/bin/env python3
"""Pack task submission zip with POSIX paths for Linux CI extraction."""

from __future__ import annotations

import zipfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent / "tasks" / "doclint-version-sync-snapshot-ledger"
OUT = Path(__file__).resolve().parent / "doclint-version-sync-snapshot-ledger.zip"

if OUT.exists():
    OUT.unlink()

with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(TASK.rglob("*")):
        if path.is_file():
            zf.write(path, path.relative_to(TASK).as_posix())

with zipfile.ZipFile(OUT) as zf:
    names = zf.namelist()
    roots = sorted({n.split("/")[0] for n in names})
    print(f"Wrote {OUT}")
    print(f"roots: {roots}")
    print(f"backslashes: {[n for n in names if chr(92) in n]}")
    print(f"environment/Dockerfile: {'environment/Dockerfile' in names}")
    print(f"tests/test.sh: {'tests/test.sh' in names}")
    print(f"total files: {len(names)}")
