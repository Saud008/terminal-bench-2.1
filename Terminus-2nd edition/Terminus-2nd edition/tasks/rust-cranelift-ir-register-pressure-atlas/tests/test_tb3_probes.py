"""Hidden TB3 probes for fluxpress."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app/scripts")
from campaign_cli import rebuild, run_bind, run_seal  # noqa: E402
from fluxpress_validate import load_config, reference_atlas  # noqa: E402


HIDDEN = Path("/opt/verifier-fixtures/fluxpress")


@pytest.fixture(scope="session", autouse=True)
def _rebuild_once():
    rebuild()
    yield


@pytest.fixture(autouse=True)
def _clean():
    shutil.rmtree("/app/scratch/ring-fluence", ignore_errors=True)
    shutil.rmtree("/app/output", ignore_errors=True)
    Path("/app/scratch/ring-fluence").mkdir(parents=True, exist_ok=True)
    Path("/app/output").mkdir(parents=True, exist_ok=True)
    yield


def _overlay_bundle(name: str) -> None:
    src = HIDDEN / f"{name}.json"
    dst = Path("/app/fixtures/rings") / f"{name}.json"
    shutil.copyfile(src, dst)


def test_hidden_spill_ring_forces_spill():
    """occupancy-scan-lemma.md: a hidden four-channel ring whose dwell windows all overlap at
    one start point must push max_occupancy above the bundle's aperture_budget and set
    spill_risk true, matching the independent Python reference math in fluxpress_validate.py."""
    _overlay_bundle("tb3_spill_ring")
    cfg = load_config()
    bundle = json.loads((HIDDEN / "tb3_spill_ring.json").read_text(encoding="utf-8"))
    exp = reference_atlas("ring-spill", bundle, cfg)
    assert exp["spill_risk"] is True
    assert run_bind("ring-spill", "tb3_spill_ring").returncode == 0
    out = "/app/output/spill.json"
    assert run_seal("ring-spill", out).returncode == 0
    got = json.loads(Path(out).read_text(encoding="utf-8"))
    assert got["closure_digest"] == exp["closure_digest"]
    assert got["spill_risk"] is True


def test_hidden_spill_ring_cleared_by_aperture_delta():
    """occupancy-scan-lemma.md: TB3_APERTURE_DELTA read fresh at seal (emit-occupancy) time can
    raise effective_aperture enough to clear a spill_risk that a plain seal would report, without
    mutating the persisted ledger's aperture_budget."""
    _overlay_bundle("tb3_spill_ring")
    cfg = load_config()
    bundle = json.loads((HIDDEN / "tb3_spill_ring.json").read_text(encoding="utf-8"))
    exp = reference_atlas("ring-spill2", bundle, cfg, aperture_delta=2)
    assert exp["spill_risk"] is False
    assert run_bind("ring-spill2", "tb3_spill_ring").returncode == 0
    out = "/app/output/spill2.json"
    env = {"TB3_APERTURE_DELTA": "2"}
    assert run_seal("ring-spill2", out, env=env).returncode == 0
    got = json.loads(Path(out).read_text(encoding="utf-8"))
    assert got["closure_digest"] == exp["closure_digest"]
    assert got["spill_risk"] is False


def test_hidden_micron_scale_env():
    """micron-ev-quantize.md: TB3_MICRON_EV_SCALE overrides the config default at accrue
    (bind) time and the persisted ledger must carry the overridden micron_ev_scale, with
    channel quantization matching the independent reference math at that scale."""
    _overlay_bundle("tb3_micron_scale_mix")
    env = {"TB3_MICRON_EV_SCALE": "200"}
    os.environ["TB3_MICRON_EV_SCALE"] = "200"
    try:
        cfg = load_config()
        assert cfg["micron_ev_scale"] == 200
        bundle = json.loads((HIDDEN / "tb3_micron_scale_mix.json").read_text(encoding="utf-8"))
        exp = reference_atlas("ring-scale", bundle, cfg)
        assert run_bind("ring-scale", "tb3_micron_scale_mix", env=env).returncode == 0
        out = "/app/output/scale.json"
        assert run_seal("ring-scale", out, env=env).returncode == 0
        got = json.loads(Path(out).read_text(encoding="utf-8"))
        assert got["closure_digest"] == exp["closure_digest"]
        art = json.loads(Path("/app/scratch/ring-fluence/ring-scale.json").read_text(encoding="utf-8"))
        assert art["micron_ev_scale"] == 200
    finally:
        os.environ.pop("TB3_MICRON_EV_SCALE", None)
