"""Subprocess driver and workspace paths for chmutled verifier."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
BIN = APP / "bin" / "chmutled"
REBUILD = APP / "scripts" / "rebuild-chledger.sh"
RESET = APP / "scripts" / "reset-state.sh"

PATHS = {
    "staging": APP / "state" / "chledger-staging.jsonl",
    "atlas": APP / "output" / "mutation-readiness-atlas.json",
    "sqlite": APP / "output" / "chledger-rows.sqlite",
    "config": APP / "fixtures" / "config",
    "meta": APP / "fixtures" / "metadata",
    "mutations": APP / "fixtures" / "mutations",
    "replicas": APP / "fixtures" / "replicas",
}

HIDDEN_ROOT = Path("/opt/verifier-fixtures/chmutled_hidden")


def fixture_dirs() -> tuple[Path, Path, Path]:
    root = os.environ.get("TB3_FIXTURE_ROOT")
    if root:
        base = Path(root)
        return base / "metadata", base / "mutations", base / "replicas"
    return PATHS["meta"], PATHS["mutations"], PATHS["replicas"]


def exec_chledger(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(BIN), *argv], capture_output=True, text=True, check=False)


def rebuild_binary() -> None:
    subprocess.run(["bash", str(REBUILD)], check=True, capture_output=True, text=True)


def wipe_workspace() -> None:
    subprocess.run(["bash", str(RESET)], check=True, capture_output=True, text=True)


def run_full_pipeline() -> None:
    wipe_workspace()
    meta, mut, rep = fixture_dirs()
    proc = exec_chledger([
        "reconcile-partitions",
        "--metadata-dir", str(meta),
        "--mutations-dir", str(mut),
        "--replica-dir", str(rep),
        "--config-dir", str(PATHS["config"]),
        "--staging", str(PATHS["staging"]),
    ])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    proc = exec_chledger([
        "emit-readiness",
        "--staging", str(PATHS["staging"]),
        "--sqlite", str(PATHS["sqlite"]),
        "--atlas", str(PATHS["atlas"]),
    ])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
