"""Persistence / generation tests for stationclos lattice materialize_generation and seal isolation."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app/scripts")
from hull_cli import rebuild, run_materialize, run_certify  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _rebuild_once():
    rebuild()
    yield


@pytest.fixture(autouse=True)
def _clean():
    shutil.rmtree("/app/work/station-hulls", ignore_errors=True)
    shutil.rmtree("/app/output", ignore_errors=True)
    Path("/app/work/station-hulls").mkdir(parents=True, exist_ok=True)
    Path("/app/output").mkdir(parents=True, exist_ok=True)
    yield


def test_materialize_generation_monotonic():
    """Repeated materialize-hulls on one campaign must increment materialize_generation in the lattice artifact."""
    assert run_materialize("camp-gen", "dual-station-basic").returncode == 0
    art1 = json.loads(Path("/app/work/station-hulls/camp-gen.json").read_text(encoding="utf-8"))
    assert art1["materialize_generation"] == 1
    assert run_materialize("camp-gen", "quantize-edge").returncode == 0
    art2 = json.loads(Path("/app/work/station-hulls/camp-gen.json").read_text(encoding="utf-8"))
    assert art2["materialize_generation"] == 2
    assert art2["bundle"] == "quantize-edge"


def test_stclos_certify_without_fixture_dir(tmp_path):
    """certify-campaign must succeed from /app/work/station-hulls alone after campaign fixtures are removed."""
    assert run_materialize("camp-iso", "dual-station-basic").returncode == 0
    # Move fixtures aside — seal must still work from lattice alone.
    campaigns = Path("/app/fixtures/campaigns")
    backup = tmp_path / "campaigns"
    shutil.move(str(campaigns), str(backup))
    try:
        out = "/app/output/iso.json"
        rc = run_certify("camp-iso", out)
        assert rc.returncode == 0, rc.stderr
        got = json.loads(Path(out).read_text(encoding="utf-8"))
        assert got["campaign_id"] == "camp-iso"
        assert len(got["rows"]) >= 1
    finally:
        shutil.move(str(backup), str(campaigns))
