"""Scan staging ledger and findings_digest contract."""

from __future__ import annotations

import json

from sarbctl_curator_contract import compute_findings_digest, load_sarif_findings, sha256_file
from sarbctl_runner import POLICY, REMAP, SARIF, STAGING, STAGING_SEQ, sarbctl_scan


def test_scan_persists_absolute_policy_and_remap_paths(clean_workspace: None) -> None:
    """finding-staging.md requires policy_path and remap_path mirror CLI absolute paths."""
    sarbctl_scan(SARIF, POLICY, REMAP, __import__("sarbctl_runner").BASELINE)
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap["policy_path"] == str(POLICY)
    assert snap["remap_path"] == str(REMAP)
    assert snap["scan_revision"] >= 1


def test_scan_revision_increments_on_repeat_scan(clean_workspace: None) -> None:
    """staging-seq.json scan_revision must bump on each successful scan."""
    sarbctl_scan(SARIF, POLICY, REMAP, __import__("sarbctl_runner").BASELINE)
    first = json.loads(STAGING.read_text(encoding="utf-8"))["scan_revision"]
    sarbctl_scan(SARIF, POLICY, REMAP, __import__("sarbctl_runner").BASELINE)
    second = json.loads(STAGING.read_text(encoding="utf-8"))["scan_revision"]
    assert second == first + 1


def test_findings_digest_matches_reference_serialization(clean_workspace: None) -> None:
    """finding-staging.md digest body must match independent reference hash."""
    sarbctl_scan(SARIF, POLICY, REMAP, __import__("sarbctl_runner").BASELINE)
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    findings = load_sarif_findings(SARIF)
    assert snap["findings_digest"] == compute_findings_digest(findings)


def test_sarif_and_policy_sha256_fields(clean_workspace: None) -> None:
    """Staging snapshot must bind raw SARIF and policy file bytes."""
    sarbctl_scan(SARIF, POLICY, REMAP, __import__("sarbctl_runner").BASELINE)
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap["sarif_sha256"] == sha256_file(SARIF)
    assert snap["policy_sha256"] == sha256_file(POLICY)


def test_staging_seq_tracks_scan_revision(clean_workspace: None) -> None:
    """staging-seq.json scan_revision must equal finding-staging scan_revision."""
    sarbctl_scan(SARIF, POLICY, REMAP, __import__("sarbctl_runner").BASELINE)
    seq = json.loads(STAGING_SEQ.read_text(encoding="utf-8"))
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert seq["scan_revision"] == snap["scan_revision"]
