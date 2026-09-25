"""Staging-focused whres tests."""

from __future__ import annotations

from resolver_cli_support import load_snapshot, pipeline, wipe
from resolver_contract_math import snapshot_digest


def test_snapshot_queries_preserved():
    """Snapshot retains query rows from scenario meta after analyze."""
    wipe()
    pipeline("constraint-range", "run-stg-1")
    snap = load_snapshot()
    assert snap["queries"][0]["package"] == "schema-kit"


def test_snapshot_target_env_fields():
    """Snapshot stores target_python and target_platform from scenario meta."""
    wipe()
    pipeline("marker-py310", "run-stg-2")
    snap = load_snapshot()
    assert snap["target_python"] == "3.10"
    assert snap["target_platform"] == "linux"


def test_snapshot_digest_matches_reference():
    """snapshot_digest reference matches CLI snapshot field per schema doc."""
    wipe()
    pipeline("httpx-pin-requests", "run-stg-3")
    snap = load_snapshot()
    expected = snapshot_digest(
        snap["run_id"],
        snap["index_fingerprint"],
        snap["target_python"],
        snap["target_platform"],
        snap["target_arch"],
        snap["packages"],
    )
    assert snap["snapshot_digest"] == expected
