#!/usr/bin/env python3
"""Pack typesense-typo-token-fuzzy-ranking-id-repair submission zip."""

from __future__ import annotations

import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASK = REPO / "tasks" / "typesense-typo-token-fuzzy-ranking-id-repair"
OUT = REPO / "tasksubmit" / "typesense-typo-token-fuzzy-ranking-id-repair.zip"

EXCLUDE_DIRS = {".pytest_cache", ".ruff_cache", "__pycache__", "target", "node_modules", "dist", "jobs"}
EXCLUDE_FILES = {"rubric.md"}

if OUT.exists():
    OUT.unlink()

count = 0
with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(TASK.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(TASK)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDE_FILES:
            continue
        zf.write(path, rel.as_posix())
        count += 1

print(f"Wrote {OUT}")
print(f"files={count} bytes={OUT.stat().st_size}")

with zipfile.ZipFile(OUT) as zf:
    names = zf.namelist()
    required = [
        "instruction.md",
        "task.toml",
        "environment/Dockerfile",
        "tests/test.sh",
        "tests/test_outputs.py",
        "solution/solve.sh",
        "solution/golden_search_stage.rs",
    ]
    for item in required:
        assert item in names, f"missing {item}"
    bad = [n for n in names if "\\" in n]
    assert not bad, bad[:5]
    print("verify ok")
