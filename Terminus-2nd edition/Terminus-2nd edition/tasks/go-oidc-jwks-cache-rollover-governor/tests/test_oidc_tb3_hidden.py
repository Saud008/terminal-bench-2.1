"""TB3 hidden traps — different failure modes than bundled scenarios."""

from __future__ import annotations

import os

import pytest

from oidc_verdict_refmath import reference_governance_report
from governor_cli_harness import OIDCGOV_HIDDEN, OIDCGOV_REPORT, oidcgov_reset_workspace, read_json, run_oidcgov_pipeline


@pytest.fixture
def tb3_fixture_dir() -> str:
    hidden = os.environ.get("TB3_FIXTURE_DIR")
    if hidden:
        return hidden
    if OIDCGOV_HIDDEN.is_dir():
        return str(OIDCGOV_HIDDEN)
    pytest.skip("hidden fixtures not mounted")


def test_oidc_tb3_grace_boundary_trap_matches_refmath(tb3_fixture_dir: str) -> None:
    """Verify hidden grace-boundary-trap accepts inclusive edge signatures per grace-window-contract.md."""
    from pathlib import Path

    oidcgov_reset_workspace()
    run_oidcgov_pipeline("grace-boundary-trap", fixture_dir=Path(tb3_fixture_dir))
    body = read_json(OIDCGOV_REPORT)
    ref = reference_governance_report("grace-boundary-trap", Path(tb3_fixture_dir))
    dec = {d["token_id"]: d for d in body["decisions"]}
    ref_dec = {d["token_id"]: d for d in ref["decisions"]}
    assert dec["edge-low"]["verdict"] == ref_dec["edge-low"]["verdict"] == "accept"
    assert dec["edge-high"]["verdict"] == ref_dec["edge-high"]["verdict"] == "accept"


def test_oidc_tb3_revoked_during_grace_trap_rejects(tb3_fixture_dir: str) -> None:
    """Verify hidden revoked-during-grace-trap rejects key_revoked before grace per revoked-key-contract.md."""
    from pathlib import Path

    oidcgov_reset_workspace()
    run_oidcgov_pipeline("revoked-during-grace-trap", fixture_dir=Path(tb3_fixture_dir))
    body = read_json(OIDCGOV_REPORT)
    dec = {d["token_id"]: d for d in body["decisions"]}
    assert dec["would-grace"]["verdict"] == "reject"
    assert dec["would-grace"]["reason_code"] == "key_revoked"
