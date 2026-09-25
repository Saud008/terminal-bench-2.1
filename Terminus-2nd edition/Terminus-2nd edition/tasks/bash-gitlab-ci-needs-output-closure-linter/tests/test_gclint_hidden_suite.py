"""Hidden fixture tests — different failure mode than bundled."""

from __future__ import annotations

import json
from pathlib import Path

from gclint_cli_support import run_pipeline, wipe


def test_hidden_tb3_duplicate_matrix_canonical():
    """Hidden matrix-duplicate overlay must flag duplicate canonical instance names."""
    wipe()
    hidden_dir = Path("/opt/verifier-fixtures/gclint/pipelines")
    run_pipeline("matrix-duplicate", "run-hidden-dup", pipeline_dir=hidden_dir)
    snap = json.loads(Path("/app/state/gclint-staging.json").read_text(encoding="utf-8"))
    assert any(j.get("duplicate") for j in snap["jobs"])


def test_hidden_matrix_rules_tb3():
    """Hidden tb3-matrix-rules overlay keeps at least one active job with valid audit_digest."""
    wipe()
    hidden_dir = Path("/opt/verifier-fixtures/gclint/pipelines")
    out = run_pipeline("tb3-matrix-rules", "run-hidden", pipeline_dir=hidden_dir)
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_jobs = json.loads(Path("/app/state/gclint-staging.json").read_text(encoding="utf-8"))["jobs"]
    active = [j for j in snap_jobs if j["active"]]
    assert len(active) >= 1
    assert rep["audit_digest"] != "broken"
