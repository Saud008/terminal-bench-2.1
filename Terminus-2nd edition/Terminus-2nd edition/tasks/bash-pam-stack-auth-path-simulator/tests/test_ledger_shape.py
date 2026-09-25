"""Ledger-focused pamtrace tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pamtrace_harness import LEDGER, run_pipeline, wipe
from pamtrace_independent_math import reference_build_ledger


@pytest.fixture(autouse=True)
def _fresh():
    wipe()
    yield


def test_pt_staging_snapshot_ledger_schema():
    """Staging snapshot on disk after compile — ledger JSON is the ingest staging artifact."""
    run_pipeline("sshd-basic", "run-stg-snap", service="sshd", subject="alice")
    snap = json.loads(LEDGER.read_text(encoding="utf-8"))
    ref = reference_build_ledger(Path("/app/fixtures/scenarios/sshd-basic"), "run-stg-snap", "sshd-basic")
    assert snap["ledger_fingerprint"] == ref["ledger_fingerprint"]
    assert "services" in snap


def test_pt_ledger_lists_all_services():
    """Ledger snapshot lists every service discovered in a multi-service scenario."""
    run_pipeline("multi-service-shared", "run-stg-1", service="sshd", subject="erin")
    snap = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert "sshd" in snap["services"]
    assert "ftp" in snap["services"]


def test_pt_ledger_preserves_outcomes():
    """Ledger retains module outcome tables from the scenario bundle after compile."""
    run_pipeline("sshd-basic", "run-stg-2", service="sshd", subject="alice")
    snap = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert "pam_unix.so" in snap["outcomes"]


def test_pt_ledger_subjects_preserved():
    """Ledger subject roster matches subjects.json from the loaded scenario."""
    run_pipeline("sudo-wheel", "run-stg-3", service="sudo", subject="alice")
    snap = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert "alice" in snap["subjects"]["users"]
