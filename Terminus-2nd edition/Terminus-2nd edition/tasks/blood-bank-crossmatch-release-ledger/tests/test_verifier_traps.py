"""Hidden traps — TB3 fixture dir."""

from __future__ import annotations

import os
from pathlib import Path

from crossmatch_spec import reference_releases
from hemo_session import HemotherapySession


def test_verifier_traps_anti_d_weak_needs_antibody_fix() -> None:
    root = Path(os.environ.get("TB3_FIXTURE_DIR", "/opt/verifier-fixtures/bbreleasectl"))
    session = HemotherapySession(fixture_dir=root)
    session.clear_workspace()
    session.run_full("hidden-anti-d-weak")
    assert session.read_ledger()["releases"] == reference_releases("hidden-anti-d-weak", root)["releases"]


def test_verifier_traps_override_authorizer_preserved() -> None:
    root = Path("/opt/verifier-fixtures/bbreleasectl")
    session = HemotherapySession(fixture_dir=root)
    session.clear_workspace()
    session.run_full("hidden-override-authorizer")
    rel = session.read_ledger()["releases"][0]
    assert rel["authorizer"] == "DR-LEE"
    assert session.read_ledger()["releases"] == reference_releases("hidden-override-authorizer", root)["releases"]
