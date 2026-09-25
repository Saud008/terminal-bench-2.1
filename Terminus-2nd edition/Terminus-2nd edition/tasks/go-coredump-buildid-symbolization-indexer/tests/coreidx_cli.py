"""Subprocess CLI helpers for coreidx verifier runs."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from coreidx_verifier_lib import DEFAULT_CATALOG, catalog_integrity_ok

APP = Path("/app")
CLI_BIN = Path("/app/bin/coreidx")
REBUILD = Path("/app/scripts/verifier-rebuild.sh")
RESET = Path("/app/scripts/reset-state.sh")
STATE = Path("/app/state/crash_staging.jsonl")
SQLITE = Path("/app/output/crash_index.sqlite")
SUMMARY = Path("/app/output/crash_summary.json")
DEFAULT_CRASHES = Path("/app/fixtures/crashes")


def crash_dir() -> Path:
    tb3 = os.environ.get("TB3_CRASH_DIR")
    return Path(tb3) if tb3 else DEFAULT_CRASHES


def catalog_for(crashes: Path) -> Path:
    hidden_cat = crashes.parent / "catalog" / "build_index.json"
    return hidden_cat if hidden_cat.is_file() else DEFAULT_CATALOG


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def rebuild() -> None:
    run(["bash", str(REBUILD)])


def reset() -> None:
    run(["bash", str(RESET)])


def pipeline(crashes: Path | None = None, catalog: Path | None = None) -> None:
    crashes = crashes or crash_dir()
    catalog = catalog or catalog_for(crashes)
    if catalog.resolve() == DEFAULT_CATALOG.resolve():
        assert catalog_integrity_ok(catalog), "catalog fixture integrity"
    reset()
    run([str(CLI_BIN), "ingest", "--crash-dir", str(crashes), "--catalog", str(catalog), "--staging", str(STATE)])
    run([str(CLI_BIN), "export", "--staging", str(STATE), "--sqlite", str(SQLITE), "--summary", str(SUMMARY)])
