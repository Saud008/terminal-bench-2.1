"""Staging-focused wgpatlas tests."""

from __future__ import annotations

import json
from pathlib import Path

from wgpatlas_cli_support import WORKSPACE, run_pipeline, wipe


def test_ingest_populates_work_artifact():
    """Verify ingest writes /app/work/{run-id}-ingest.json work artifact."""
    wipe()
    from wgpatlas_cli_support import invoke, CLI
    invoke([str(CLI), "ingest", "--site", "coastal-mesh", "--run-id", "run-ing"])
    assert Path("/app/work/run-ing-ingest.json").is_file()


def test_analyze_requires_prior_ingest():
    """Verify analyze fails when ingest artifact is missing for the run id."""
    wipe()
    from wgpatlas_cli_support import invoke, CLI
    proc = invoke([str(CLI), "analyze", "--run-id", "missing"])
    assert proc.returncode != 0


def test_workspace_includes_route_conflicts_array():
    """Verify workspace snapshot includes route_conflicts array after table-split analyze."""
    wipe()
    run_pipeline("table-split", "run-rc")
    snap = json.loads(WORKSPACE.read_text(encoding="utf-8"))
    assert "route_conflicts" in snap
    assert isinstance(snap["route_conflicts"], list)


def test_overlaps_sorted_lexicographically():
    """Verify overlap edges sort by peer_a peer_b cidr_a cidr_b per allowed-ip-overlap-contract."""
    wipe()
    run_pipeline("coastal-mesh", "run-ov-sort")
    snap = json.loads(WORKSPACE.read_text(encoding="utf-8"))
    keys = [(o["peer_a"], o["peer_b"], o["cidr_a"], o["cidr_b"]) for o in snap["overlaps"]]
    assert keys == sorted(keys)
