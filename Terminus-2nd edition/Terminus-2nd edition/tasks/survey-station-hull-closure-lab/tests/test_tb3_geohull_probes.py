"""Hidden TB3 probes for stationclos dateline wrap and TB3_MICRO_SCALE overrides."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app/scripts")
from hull_cli import rebuild, run_materialize, run_certify  # noqa: E402
from stationclos_validate import expected_atlas, load_config  # noqa: E402


HIDDEN = Path("/opt/verifier-fixtures/stationclos")


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


def _overlay_bundle(name: str) -> None:
    src = HIDDEN / f"{name}.json"
    dst = Path("/app/fixtures/campaigns") / f"{name}.json"
    shutil.copyfile(src, dst)


def test_stclos_opt_dateline_parts():
    """Hidden dateline-wrap bundle must partition and match reference closure_digest."""
    assert str(HIDDEN).startswith("/opt/verifier-fixtures")
    _overlay_bundle("dateline-wrap")
    cfg = load_config()
    bundle = json.loads((HIDDEN / "dateline-wrap.json").read_text(encoding="utf-8"))
    exp = expected_atlas("camp-dl", bundle, cfg)
    assert exp is not None
    assert run_materialize("camp-dl", "dateline-wrap").returncode == 0
    out = "/app/output/dl.json"
    assert run_certify("camp-dl", out).returncode == 0
    got = json.loads(Path(out).read_text(encoding="utf-8"))
    assert got["closure_digest"] == exp["closure_digest"]
    assert got["summary"]["wrap_parts"] >= 2


def test_stclos_opt_micro_scale_override():
    """TB3_MICRO_SCALE must drive lattice microdegree_scale and seal digests for micro-scale-mix."""
    _overlay_bundle("micro-scale-mix")
    env = {"TB3_MICRO_SCALE": "5000"}
    os.environ["TB3_MICRO_SCALE"] = "5000"
    try:
        cfg = load_config()
        assert cfg["microdegree_scale"] == 5000
        bundle = json.loads((HIDDEN / "micro-scale-mix.json").read_text(encoding="utf-8"))
        exp = expected_atlas("camp-ms", bundle, cfg)
        assert exp is not None
        assert run_materialize("camp-ms", "micro-scale-mix", env=env).returncode == 0
        out = "/app/output/ms.json"
        assert run_certify("camp-ms", out, env=env).returncode == 0
        got = json.loads(Path(out).read_text(encoding="utf-8"))
        assert got["closure_digest"] == exp["closure_digest"]
        art = json.loads(Path("/app/work/station-hulls/camp-ms.json").read_text(encoding="utf-8"))
        assert art["microdegree_scale"] == 5000
    finally:
        os.environ["TB3_MICRO_SCALE"] = "10000"
