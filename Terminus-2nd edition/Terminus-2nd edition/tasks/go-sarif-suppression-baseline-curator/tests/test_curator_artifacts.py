"""Artifact path contract after a full sarbctl run."""

from __future__ import annotations

import json

from sarbctl_runner import (
    BASELINE_REV,
    DELTA_OUT,
    REJECTED,
    STAGING,
    sarbctl_full_run,
)


def test_curator_writes_all_instruction_artifact_paths(clean_workspace: None) -> None:
    """Instruction requires finding-staging, baseline-revision, finding-delta, and rejected-findings paths."""
    sarbctl_full_run(
        __import__("sarbctl_runner").SARIF,
        __import__("sarbctl_runner").POLICY,
        __import__("sarbctl_runner").REMAP,
        __import__("sarbctl_runner").BASELINE,
    )
    assert str(STAGING) == "/app/state/finding-staging.json"
    assert str(BASELINE_REV) == "/app/state/reconcile-revision.json"
    assert str(DELTA_OUT) == "/app/output/finding-delta.json"
    assert str(REJECTED) == "/app/output/rejected-findings.jsonl"
    assert STAGING.is_file() and BASELINE_REV.is_file() and DELTA_OUT.is_file() and REJECTED.is_file()
    delta = json.loads(DELTA_OUT.read_text(encoding="utf-8"))
    assert len(delta["delta_digest"]) == 64
