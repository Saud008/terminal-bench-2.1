"""Policy graph intermediate probes for mpiqctl."""

from __future__ import annotations

import json
from pathlib import Path

from permit_queue_driver import FIXTURE_ROOT, invoke


def test_mpq_compliance_trace_artifact(fresh_insp_state) -> None:
    """compile-policy must write /app/intermediate/compliance-trace.json."""
    invoke(["snapshot-load", "--scenario", "clean-queue", "--fixture-dir", str(FIXTURE_ROOT)])
    proc = invoke(["compile-policy", "--scenario", "clean-queue"])
    assert proc.returncode == 0
    walk = json.loads(Path("/app/intermediate/compliance-trace.json").read_text(encoding="utf-8"))
    assert walk.get("version") == 2
    assert len(walk.get("walk", [])) >= 6


def test_mpq_policy_graph_lane_count(fresh_insp_state) -> None:
    """policy-graph.json must list one edge per permit route in bundled scenario."""
    invoke(["snapshot-load", "--scenario", "clean-queue", "--fixture-dir", str(FIXTURE_ROOT)])
    proc = invoke(["compile-policy", "--scenario", "clean-queue"])
    assert proc.returncode == 0
    graph = json.loads(Path("/app/work/policy-graph.json").read_text(encoding="utf-8"))
    assert len(graph["edges"]) >= 6


def test_mpq_hold_mask_precedence_shape(fresh_insp_state) -> None:
    """hold-mask.json must map district_id to numeric hold rank."""
    invoke(["snapshot-load", "--scenario", "zoning-hold-block", "--fixture-dir", str(FIXTURE_ROOT)])
    proc = invoke(["apply-holds", "--scenario", "zoning-hold-block"])
    assert proc.returncode == 0
    mask = json.loads(Path("/app/work/hold-mask.json").read_text(encoding="utf-8"))
    assert all(isinstance(v, int) for v in mask.values())
