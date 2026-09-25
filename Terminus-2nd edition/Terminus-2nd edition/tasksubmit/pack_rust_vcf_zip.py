#!/usr/bin/env python3
"""Pack rust-vcf-haplotype-block-consistency-auditor submission zip with POSIX paths."""

from __future__ import annotations

import zipfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent / "tasks" / "rust-vcf-haplotype-block-consistency-auditor"
OUT = Path(__file__).resolve().parent / "rust-vcf-haplotype-block-consistency-auditor.zip"
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
        "environment/Cargo.lock",
        "tests/test.sh",
        "tests/test_outputs.py",
        "tests/verifier-fixtures/vcfaud/vcf/tb3-ps-salt/variants.vcf",
        "solution/solve.sh",
    ]
    missing = [r for r in required if r not in names]
    bad = [n for n in names if chr(92) in n]
    ruff = [n for n in names if ".ruff_cache" in n]
    print(f"Wrote {OUT}")
    print(f"bytes: {OUT.stat().st_size}")
    print(f"total files: {len(names)}")
    print(f"missing required: {missing}")
    print(f"backslashes: {bad}")
    print(f"ruff_cache entries: {len(ruff)}")
    if missing or bad or ruff:
        raise SystemExit(1)
