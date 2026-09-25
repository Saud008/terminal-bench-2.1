"""Smoke coverage for xsnapctl ingest staging."""

from __future__ import annotations

from xsnap_refmath import read_json, reference_staging
from xsnap_session import XSNAP_BIN, XSNAP_FIX, XSNAP_STAGE, invoke_xsnap, reset_xsnap_workspace


def test_xsnapctl_staging_digest_on_pair_load() -> None:
    """ingest-pair writes xds-staging.json with contract digest."""
    reset_xsnap_workspace()
    proc = invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "match-precedence", "--fixture-dir", str(XSNAP_FIX)])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert XSNAP_STAGE.is_file()
    body = read_json(XSNAP_STAGE)
    ref = reference_staging("match-precedence", XSNAP_FIX)
    assert body["staging_digest"] == ref["staging_digest"]


def test_xsnapctl_left_payload_matches_fixture() -> None:
    """Staged left snapshot equals scenario left.json payload."""
    reset_xsnap_workspace()
    invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "stable-diff-pair", "--fixture-dir", str(XSNAP_FIX)])
    body = read_json(XSNAP_STAGE)
    fixture = read_json(XSNAP_FIX / "scenarios/stable-diff-pair/left.json")
    assert body["left"]["routes"] == fixture["routes"]
