"""Emit-stage delta categories and reference parity."""

from __future__ import annotations

import json

from sarbctl_curator_contract import load_sarif_findings, reference_delta
from sarbctl_runner import (
    BASELINE,
    DELTA_OUT,
    POLICY,
    REMAP,
    SARIF,
    CLI,
    invoke,
    sarbctl_full_run,
    sarbctl_scan,
)


def test_emit_rows_match_independent_reference(clean_workspace: None) -> None:
    """delta-export.md categories must match sarbctl_curator_contract delta builder."""
    sarbctl_full_run(SARIF, POLICY, REMAP, BASELINE)
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    remap_cfg = json.loads(REMAP.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    want = reference_delta(load_sarif_findings(SARIF), baseline, policy, remap_cfg)
    body = json.loads(DELTA_OUT.read_text(encoding="utf-8"))
    got = sorted(body["rows"], key=lambda r: (r["category"], r["finding_id"]))
    assert got == want


def test_emit_reports_removed_baseline_finding(clean_workspace: None) -> None:
    """Removed baseline rows absent from curated scan must appear as removed category."""
    sarbctl_full_run(SARIF, POLICY, REMAP, BASELINE)
    body = json.loads(DELTA_OUT.read_text(encoding="utf-8"))
    assert any(r["category"] == "removed" and r["finding_id"] == "b-003" for r in body["rows"])


def test_emit_refuses_before_curate_generation(clean_workspace: None) -> None:
    """emit must fail when reconcile_revision is zero and baseline-revision missing."""
    sarbctl_scan(SARIF, POLICY, REMAP, BASELINE)
    proc = invoke([str(CLI), "emit"])
    assert proc.returncode != 0
