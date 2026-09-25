"""Staging snapshot contract tests."""

from __future__ import annotations

import json

from gclint_cli_support import STAGING, run_pipeline, wipe


def test_staging_jobs_have_stage_field():
    """Each staging job record includes name and stage per staging-snapshot-schema.md."""
    wipe()
    run_pipeline("matrix-basic", "run-alpha")
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    for job in snap["jobs"]:
        assert "stage" in job
        assert "name" in job


def test_staging_stages_array_present():
    """artifact-chain staging preserves ordered stages array from pipeline YAML."""
    wipe()
    run_pipeline("artifact-chain", "run-alpha")
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap["stages"] == ["build", "package", "publish"]
