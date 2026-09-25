"""Route match precedence contract tests."""

from __future__ import annotations

import pytest

from xsnap_refmath import read_json, reference_staging
from xsnap_session import (
    XSNAP_BIN,
    XSNAP_FIX,
    XSNAP_NORM_L,
    XSNAP_STAGE,
    drive_xsnap_triple,
    invoke_xsnap,
    reset_xsnap_workspace,
)

BUNDLED = (
    "match-precedence",
    "weight-normalize",
    "filter-chain-order",
    "sds-ref-resolve",
    "stable-diff-pair",
    "idempotent-export",
)


@pytest.mark.parametrize("scenario", BUNDLED)
def test_xsnapctl_scenario_seal_digest(scenario: str) -> None:
    """Each bundled scenario staging digest matches xsnap_refmath."""
    reset_xsnap_workspace()
    proc = invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", scenario, "--fixture-dir", str(XSNAP_FIX)])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = read_json(XSNAP_STAGE)
    assert body["staging_digest"] == reference_staging(scenario, XSNAP_FIX)["staging_digest"]


def test_xsnapctl_longer_prefix_wins_tie() -> None:
    """Canonical routes keep highest-precedence prefix match per cluster."""
    reset_xsnap_workspace()
    drive_xsnap_triple("match-precedence")
    routes = read_json(XSNAP_NORM_L)["routes"][0]["routes"]
    api = next(r for r in routes if r["cluster"] == "api")
    assert "/api/v1" in api["match"].get("prefix", "")
