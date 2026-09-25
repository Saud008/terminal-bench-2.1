"""Curate-stage policy, dedupe, remap, and rejection behavior."""

from __future__ import annotations

import json

from sarbctl_runner import (
    BASELINE,
    BASELINE_REV,
    POLICY,
    REMAP,
    REJECTED,
    SARIF,
    sarbctl_curate,
    sarbctl_full_run,
    sarbctl_scan,
    wipe_state,
)


def test_dedupe_collapse_prefers_error_severity(clean_workspace: None) -> None:
    """dedupe-collapse.md keeps highest severity for duplicate rule_key uri line."""
    wipe_state()
    sarbctl_scan(SARIF, POLICY, REMAP, BASELINE)
    sarbctl_curate()
    rev = json.loads(BASELINE_REV.read_text(encoding="utf-8"))
    row = next(e for e in rev["entries"] if e["uri"] == "src/main.py" and e["start_line"] == 10)
    assert row["finding_id"] == "f-002" and row["level"] == "error"


def test_path_remap_strips_ci_runner_prefix(clean_workspace: None) -> None:
    """path-remap.md longest prefix_strip must normalize util.go CI absolute path."""
    wipe_state()
    sarbctl_scan(SARIF, POLICY, REMAP, BASELINE)
    sarbctl_curate()
    rev = json.loads(BASELINE_REV.read_text(encoding="utf-8"))
    row = next(e for e in rev["entries"] if e["finding_id"] == "f-003")
    assert row["uri"] == "internal/util.go"


def test_rule_alias_canonicalization(clean_workspace: None) -> None:
    """rule-canonicalization.md maps @v2 alias to canonical exec-detected rule."""
    wipe_state()
    sarbctl_scan(SARIF, POLICY, REMAP, BASELINE)
    sarbctl_curate()
    rev = json.loads(BASELINE_REV.read_text(encoding="utf-8"))
    row = next(e for e in rev["entries"] if e["finding_id"] == "f-002")
    assert row["rule_key"] == "semgrep:python.lang.security.audit.exec-detected"


def test_suppression_expired_finding_rejected(clean_workspace: None) -> None:
    """suppression-expiry.md rejects f-004 after suppress_until window ends."""
    sarbctl_full_run(SARIF, POLICY, REMAP, BASELINE)
    rows = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(r["finding_id"] == "f-004" and r["reason"] == "suppression_expired" for r in rows)


def test_curate_flags_exec_duplicate_as_drift(clean_workspace: None) -> None:
    """fingerprint-drift.md marks baseline fingerprint mismatch on collapsed exec row."""
    wipe_state()
    sarbctl_scan(SARIF, POLICY, REMAP, BASELINE)
    sarbctl_curate()
    rev = json.loads(BASELINE_REV.read_text(encoding="utf-8"))
    row = next(e for e in rev["entries"] if e["finding_id"] == "f-002")
    assert row["drift_from_baseline"] is True


def test_baseline_revision_positive_generation(clean_workspace: None) -> None:
    """delta-export.md requires reconcile_revision greater than zero before emit."""
    sarbctl_full_run(SARIF, POLICY, REMAP, BASELINE)
    rev = json.loads(BASELINE_REV.read_text(encoding="utf-8"))
    assert rev["reconcile_revision"] >= 1
