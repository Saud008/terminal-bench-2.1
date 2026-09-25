"""TB3 hidden traps — different failure modes than bundled scenarios."""

from __future__ import annotations

import os

import pytest

from clerkdesk_refmath import reference_atlas_report
from clerkdesk_cli import CLERK_ATLAS, CLERK_HIDDEN, clerkdesk_reset, read_json, run_clerkdesk_pipeline


@pytest.fixture
def tb3_fixture_dir() -> str:
    hidden = os.environ.get("TB3_FIXTURE_DIR")
    if hidden:
        return hidden
    if CLERK_HIDDEN.is_dir():
        return str(CLERK_HIDDEN)
    pytest.skip("hidden fixtures not mounted")


def test_clerkredact_verify_alias_cycle_trap_matches_refmath(tb3_fixture_dir: str) -> None:
    """Hidden alias-cycle-trap scenario must match independent reference atlas per verifier-refmath-contract."""
    from pathlib import Path

    clerkdesk_reset()
    run_clerkdesk_pipeline("alias-cycle-trap", fixture_dir=Path(tb3_fixture_dir))
    body = read_json(CLERK_ATLAS)
    ref = reference_atlas_report("alias-cycle-trap", Path(tb3_fixture_dir))
    assert body["findings"] == ref["findings"]


def test_clerkredact_verify_sealed_nested_trap_matches_refmath(tb3_fixture_dir: str) -> None:
    """Hidden sealed-nested-trap honors TB3_SEALED_BIAS sensitivity per verifier-refmath-contract."""
    from pathlib import Path

    clerkdesk_reset()
    os.environ["TB3_SEALED_BIAS"] = "1.0"
    try:
        run_clerkdesk_pipeline("sealed-nested-trap", fixture_dir=Path(tb3_fixture_dir))
    finally:
        os.environ.pop("TB3_SEALED_BIAS", None)
    body = read_json(CLERK_ATLAS)
    ref = reference_atlas_report("sealed-nested-trap", Path(tb3_fixture_dir))
    assert body["finding_count"] == ref["finding_count"]
    assert body["findings"][0]["term"] == ref["findings"][0]["term"]
