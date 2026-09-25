"""Workspace snapshot and staging contract tests."""

from __future__ import annotations

import json

from crpe_cli_support import APP, run_pipeline, wipe


def test_staging_includes_crush_and_pool():
    """Verify normalized snapshot retains crush pool and osd sections."""
    wipe()
    run_pipeline("coastal-pool", "run-staging", 0, 0)
    snap = json.loads((APP / "state/crpe-normalized.json").read_text(encoding="utf-8"))
    assert "crush" in snap and "pool" in snap and "osd" in snap


def test_work_loaded_file_created_on_ingest():
    """Verify ingest writes work run-id loaded json after map bundle ingest."""
    wipe()
    run_pipeline("coastal-pool", "run-work", 0, 0)
    assert (APP / "work/run-work-loaded.json").is_file()
