#!/usr/bin/env python3
"""Pack authoritative-replication-lag-compensation-buffer-repair submission zip."""

from __future__ import annotations

import zipfile
from pathlib import Path

TASK = (
    Path(__file__).resolve().parent.parent
    / "tasks"
    / "authoritative-replication-lag-compensation-buffer-repair"
)
OUT = (
    Path(__file__).resolve().parent
    / "authoritative-replication-lag-compensation-buffer-repair.zip"
)
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "target",
    "output",
    "state",
    "data",
    "jobs",
}
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
        "environment/Cargo.lock",
        "tests/test.sh",
        "tests/test_outputs.py",
        "tests/reference_lag.py",
        "solution/solve.sh",
        "environment/docs/lag-estimator.md",
        "environment/fixtures/traces/baseline_ingest.jsonl",
    ]
    missing = [r for r in required if r not in names]
    bad = [n for n in names if chr(92) in n]
    nested = [
        n
        for n in names
        if n.startswith("authoritative-replication-lag-compensation-buffer-repair/")
    ]
    print(f"Wrote {OUT}")
    print(f"bytes: {OUT.stat().st_size}")
    print(f"total files: {len(names)}")
    print(f"missing required: {missing}")
    print(f"backslashes: {bad}")
    print(f"nested wrapper entries: {len(nested)}")
    if missing or bad or nested:
        raise SystemExit(1)
