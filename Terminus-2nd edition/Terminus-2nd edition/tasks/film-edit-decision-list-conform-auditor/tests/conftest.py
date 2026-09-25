"""Shared pytest fixtures for edl-conform-audit ingest stage and export publish verifier."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

APP = Path("/app")
CLI = Path("/usr/local/bin/edl-conform-audit")
BUNDLES = APP / "fixtures/bundles"
OUTPUT = APP / "output"
STATE = APP / "state"
RESET = APP / "scripts/reset-state.sh"
TB3 = Path("/opt/verifier-fixtures/tb3-bundles")
LIB = APP / "lib"

BUNDLED_IDS = [
    "clean-conform",
    "df-cross-cut",
    "alias-reverse",
    "handle-overflow",
    "missing-suppress",
    "pulldown-trap",
]

OUTPUT_ATLAS_PATH = "/app/output/conform-atlas.json"
STATE_SEALED = "/app/state/edl-conform-sealed.json"
STATE_RUN_SEQ = "/app/state/run-seq.json"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def bundle_manifest(bundle_id: str) -> Path:
    if bundle_id == "df-minute-boundary":
        return TB3 / "df-minute-boundary" / "bundle.json"
    if bundle_id == "alias-missing-order":
        return TB3 / "alias-missing-order" / "bundle.json"
    return BUNDLES / bundle_id / "bundle.json"


def stage_cli(bundle_id: str) -> subprocess.CompletedProcess[str]:
    manifest = bundle_manifest(bundle_id)
    return run([str(CLI), "stage", "--bundle", str(manifest)])


def publish_cli(bundle_id: str, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([str(CLI), "publish", "--bundle", bundle_id, "--output", str(out)])


def load_sealed() -> dict[str, Any]:
    return json.loads((STATE / "edl-conform-sealed.json").read_text(encoding="utf-8"))


def load_staged_snapshot() -> dict[str, Any]:
    return load_sealed()


def seal_digest_from_staging_file() -> str:
    from conform_frame_oracle import compute_seal_digest

    staging = load_sealed()
    return compute_seal_digest(staging["edits"], staging["diagnostics"])


@pytest.fixture(autouse=True)
def reset_state() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr
    yield
    run(["bash", str(RESET)])
