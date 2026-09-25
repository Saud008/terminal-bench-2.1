"""Shared pytest fixtures for CT witness auditor."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
BIN = APP / "bin" / "ctwrelease"
BUILD = APP / "environment" / "scripts" / "rebuild_ctwrelease.sh"
ROWS = APP / "state" / "checkpoint_rows.json"
ARCHIVE = APP / "output" / "witness_evidence_archive.json"
DEFAULT_INDEX = APP / "environment" / "fixtures" / "audit_index.json"
DEFAULT_LEDGER = APP / "environment" / "fixtures" / "witness_ledger.json"
HIDDEN_ROOT = Path("/opt/verifier-fixtures/ct_hidden")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


@pytest.fixture(scope="session")
def cli_binary() -> Path:
    run(["bash", str(BUILD)])
    assert BIN.is_file()
    return BIN


@pytest.fixture
def audit_paths() -> tuple[Path, Path]:
    idx = Path(os.environ["TB3_AUDIT_INDEX"]) if os.environ.get("TB3_AUDIT_INDEX") else DEFAULT_INDEX
    led = Path(os.environ["TB3_WITNESS_LEDGER"]) if os.environ.get("TB3_WITNESS_LEDGER") else DEFAULT_LEDGER
    return idx, led


@pytest.fixture
def pipeline_archive(cli_binary: Path, audit_paths: tuple[Path, Path]) -> dict:
    index_path, ledger_path = audit_paths
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    for target in (ROWS, ARCHIVE):
        if target.exists():
            target.unlink()
    run(
        [
            str(cli_binary),
            "stage",
            "--audit-index",
            str(index_path),
            "--witness-ledger",
            str(ledger_path),
            "--staging",
            str(ROWS),
        ]
    )
    run([str(cli_binary), "seal", "--staging", str(ROWS), "--out", str(ARCHIVE)])
    return json.loads(ARCHIVE.read_text(encoding="utf-8"))
