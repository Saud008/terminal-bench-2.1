"""Harbor pytest entrypoint for airclos scientific closure-lab verification."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from atlas_lab_harness import (
    ATLAS_BIN,
    BUNDLED_SCENARIOS,
    CAMPAIGN_BINDING,
    CHRONO_CLOSURE,
    CLOSURE_ATLAS,
    CLOSURE_LATTICE,
    LAB_FIXTURES,
    LAB_HIDDEN,
    SEAL_EPOCH,
    lab_cli,
    lab_reset_workspace,
    read_json,
    run_closure_pipeline,
)
from closure_refmath import (
    active_at,
    expand_route,
    load_scenario,
    normalize_runway,
    point_in_polygon,
    reference_binding_digest,
    reference_impact_atlas,
    suppress_amendments,
)


def test_closure_bind_writes_campaign_binding() -> None:
    """Numeric campaign bind writes /app/state/campaign-binding.json per campaign-binding-contract.md."""
    lab_reset_workspace()
    proc = lab_cli(
        [
            ATLAS_BIN,
            "bind-campaign",
            "--scenario",
            "amend-latest-wins",
            "--fixture-dir",
            str(LAB_FIXTURES),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert CAMPAIGN_BINDING.is_file()


@pytest.mark.parametrize("scenario_id", BUNDLED_SCENARIOS)
def test_closure_binding_digest_matches_refmath(scenario_id: str) -> None:
    """Binding digest matches independent numeric reference math for each bundled campaign."""
    lab_reset_workspace()
    proc = lab_cli(
        [
            ATLAS_BIN,
            "bind-campaign",
            "--scenario",
            scenario_id,
            "--fixture-dir",
            str(LAB_FIXTURES),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(CAMPAIGN_BINDING.read_text(encoding="utf-8"))
    ref = reference_binding_digest(scenario_id, LAB_FIXTURES)
    assert body["binding_digest"] == ref


def test_closure_amend_keeps_highest_active() -> None:
    """Amendment closure residual keeps one active NOTAM per series per amendment-closure-lemma.md."""
    lab_reset_workspace()
    run_closure_pipeline("amend-latest-wins")
    atlas = read_json(CLOSURE_ATLAS)
    assert atlas["active_notam_count"] == 1
    assert atlas["route_closures"]


def test_closure_midnight_window_route_rows() -> None:
    """Crossing-midnight chronology windows generate route closures per chronology-window-lemma.md."""
    lab_reset_workspace()
    run_closure_pipeline("midnight-window-active")
    atlas = read_json(CLOSURE_ATLAS)
    ref = reference_impact_atlas("midnight-window-active", LAB_FIXTURES)
    assert len(atlas["route_closures"]) == len(ref["route_closures"]) >= 1


def test_closure_sector_l_shape_penetration() -> None:
    """Numeric ray-cast sector penetration on concave polygons per sector-spatial-lemma.md."""
    lab_reset_workspace()
    run_closure_pipeline("sector-fix-inside")
    atlas = read_json(CLOSURE_ATLAS)
    assert "SEC-L" in atlas["sealed_sectors"]
    assert any(r["impact_code"] == "sector_penetration" for r in atlas["route_closures"])


def test_closure_runway_normalize_match() -> None:
    """Normalized runway designators match closures per runway-normalization-lemma.md."""
    lab_reset_workspace()
    run_closure_pipeline("runway-normalize-match")
    atlas = read_json(CLOSURE_ATLAS)
    assert any(r["impact_code"] == "runway_closure" for r in atlas["route_closures"])


def test_closure_airway_expand_mid_fix() -> None:
    """Airway catalog expansion exposes MID fix closures per airway-expansion-lemma.md."""
    lab_reset_workspace()
    run_closure_pipeline("airway-catalog-expand")
    atlas = read_json(CLOSURE_ATLAS)
    assert any(r["detail"] == "MID" for r in atlas["route_closures"])


def test_closure_inactive_window_zero_rows() -> None:
    """Inactive chronology windows produce zero route closures per chronology-window-lemma.md."""
    lab_reset_workspace()
    run_closure_pipeline("inactive-window-skip")
    atlas = read_json(CLOSURE_ATLAS)
    assert atlas["active_notam_count"] == 0
    assert atlas["route_closures"] == []


def test_closure_multi_flight_mixed_codes() -> None:
    """Mixed runway and sector closures across multiple flights in one campaign."""
    lab_reset_workspace()
    run_closure_pipeline("multi-flight-mixed")
    atlas = read_json(CLOSURE_ATLAS)
    codes = {r["impact_code"] for r in atlas["route_closures"]}
    assert "runway_closure" in codes
    assert "sector_penetration" in codes


def test_closure_seal_epoch_positive_after_fold() -> None:
    """fold-closure increments seal_epoch residual per atlas-seal-contract.md."""
    lab_reset_workspace()
    run_closure_pipeline("stable-repeat-report")
    epoch = read_json(SEAL_EPOCH)
    assert epoch["seal_epoch"] > 0


def test_closure_atlas_digest_matches_refmath() -> None:
    """atlas_digest matches independent numeric reference math per atlas-seal-contract.md."""
    lab_reset_workspace()
    run_closure_pipeline("stable-repeat-report")
    atlas = read_json(CLOSURE_ATLAS)
    ref = reference_impact_atlas("stable-repeat-report", LAB_FIXTURES)
    assert atlas["atlas_digest"] == ref["atlas_digest"]


def test_closure_repeat_seal_byte_stable() -> None:
    """Repeat seal-atlas is byte-stable per repeat-seal-contract.md."""
    lab_reset_workspace()
    run_closure_pipeline("stable-repeat-report")
    first = CLOSURE_ATLAS.read_bytes()
    proc = lab_cli([ATLAS_BIN, "seal-atlas", "--scenario", "stable-repeat-report"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    second = CLOSURE_ATLAS.read_bytes()
    assert first == second


def test_closure_chronology_state_written() -> None:
    """close-chronology writes /app/state/chronology-closure.json."""
    lab_reset_workspace()
    run_closure_pipeline("amend-latest-wins")
    assert CHRONO_CLOSURE.is_file()
    closure = read_json(CHRONO_CLOSURE)
    assert closure["scenario"] == "amend-latest-wins"
    assert "active_notams" in closure


def test_closure_lattice_state_written() -> None:
    """fold-closure writes /app/state/closure-lattice.json per atlas-seal-contract.md."""
    lab_reset_workspace()
    run_closure_pipeline("amend-latest-wins")
    assert CLOSURE_LATTICE.is_file()
    lattice = read_json(CLOSURE_LATTICE)
    assert lattice["scenario"] == "amend-latest-wins"


def test_closure_seal_blocked_without_fold() -> None:
    """seal-atlas is blocked when seal_epoch is zero per atlas-seal-contract.md."""
    lab_reset_workspace()
    proc = lab_cli(
        [
            ATLAS_BIN,
            "bind-campaign",
            "--scenario",
            "amend-latest-wins",
            "--fixture-dir",
            str(LAB_FIXTURES),
        ]
    )
    assert proc.returncode == 0
    proc2 = lab_cli([ATLAS_BIN, "seal-atlas", "--scenario", "amend-latest-wins"])
    assert proc2.returncode != 0


@pytest.mark.parametrize("scenario_id", BUNDLED_SCENARIOS)
def test_closure_full_atlas_matches_refmath(scenario_id: str) -> None:
    """Full impact-closure atlas matches numeric reference math for each bundled campaign."""
    lab_reset_workspace()
    run_closure_pipeline(scenario_id)
    atlas = read_json(CLOSURE_ATLAS)
    ref = reference_impact_atlas(scenario_id, LAB_FIXTURES)
    assert atlas["sealed_sectors"] == ref["sealed_sectors"]
    assert atlas["route_closures"] == ref["route_closures"]
    assert atlas["active_notam_count"] == ref["active_notam_count"]


def test_numeric_lemma_amend_keeps_highest() -> None:
    """Unit: amendment closure keeps highest amendment per series_id."""
    rows = [
        {"series_id": "S", "amendment": 1, "notam_id": "A"},
        {"series_id": "S", "amendment": 3, "notam_id": "B"},
    ]
    out = suppress_amendments(rows)
    assert len(out) == 1
    assert out[0]["amendment"] == 3


def test_numeric_lemma_chronology_window_wraps() -> None:
    """Unit: crossing-midnight activation windows per chronology-window-lemma.md."""
    assert active_at(1380, 90, 30) is True
    assert active_at(1380, 90, 500) is False


def test_numeric_lemma_runway_normalize_strips_zeros() -> None:
    """Unit: runway designator normalization per runway-normalization-lemma.md."""
    assert normalize_runway("09L") == "9L"
    assert normalize_runway("9l") == "9L"


def test_numeric_lemma_spatial_ray_cast_inside_l_shape() -> None:
    """Unit: ray-cast point-in-polygon residual for concave sectors."""
    poly = [
        {"x": 0, "y": 0},
        {"x": 4, "y": 0},
        {"x": 4, "y": 2},
        {"x": 2, "y": 2},
        {"x": 2, "y": 4},
        {"x": 0, "y": 4},
    ]
    assert point_in_polygon(1, 3, poly) is True
    assert point_in_polygon(3, 3, poly) is False


def test_numeric_lemma_airway_expand_inserts_mid_fix() -> None:
    """Unit: airway catalog expansion per airway-expansion-lemma.md."""
    catalog = {"AWY-7": ["DEP", "MID", "ARR"]}
    out = expand_route(["DEP", "AWY-7", "ARR"], catalog)
    assert out == ["DEP", "MID", "ARR"]


def test_numeric_lemma_sector_fixture_polygon_ref() -> None:
    """Unit: bundled sector-fix-inside fixture point lies inside its NOTAM polygon."""
    data = load_scenario("sector-fix-inside", LAB_FIXTURES)
    inner = data["fix_points"][0]
    poly = data["notams"][0]["polygon"]
    assert point_in_polygon(inner["x"], inner["y"], poly) is True


@pytest.fixture
def hidden_fixture_dir() -> str:
    hidden = os.environ.get("LAB_FIXTURE_DIR")
    if hidden:
        return hidden
    if LAB_HIDDEN.is_dir():
        return str(LAB_HIDDEN)
    pytest.skip("hidden fixtures not mounted")


def test_closure_probe_midnight_edge_inclusive(hidden_fixture_dir: str) -> None:
    """Hidden midnight-edge-eq accepts inclusive end-minute boundary (chronology closure)."""
    lab_reset_workspace()
    run_closure_pipeline("midnight-edge-eq", fixture_dir=Path(hidden_fixture_dir))
    body = read_json(CLOSURE_ATLAS)
    ref = reference_impact_atlas("midnight-edge-eq", Path(hidden_fixture_dir))
    assert body["route_closures"] == ref["route_closures"]
    assert len(body["route_closures"]) >= 1


def test_closure_probe_amend_zero_series_prefers_three(hidden_fixture_dir: str) -> None:
    """Hidden amend-zero-series-trap keeps amendment 3 over 0 (amendment closure residual)."""
    lab_reset_workspace()
    run_closure_pipeline("amend-zero-series-trap", fixture_dir=Path(hidden_fixture_dir))
    body = read_json(CLOSURE_ATLAS)
    ref = reference_impact_atlas("amend-zero-series-trap", Path(hidden_fixture_dir))
    ids = {r["flight_id"] for r in body["route_closures"]}
    assert "T2A" in ids
    assert "T2B" not in ids
    assert body["route_closures"] == ref["route_closures"]
