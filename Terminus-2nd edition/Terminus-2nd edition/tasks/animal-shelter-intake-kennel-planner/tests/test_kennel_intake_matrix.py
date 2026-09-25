"""Parametrized shelter intake matrix — bind, weave, seal vs reference math."""

from __future__ import annotations

import json

import pytest

from kennel_session import ATLAS_JSON, FIXTURE_ROOT, SCENARIO_CLEAN, run_pipeline, wipe_state
from shelter_planner_sim import reference_atlas

MATRIX_SCENARIOS = (
    "clean-intake",
    "overflow-single",
    "quarantine-block",
    "hold-precedence",
    "species-upgrade",
    "priority-ranking",
    "transfer-penalty-tie",
    "stable-rerun",
)


@pytest.mark.parametrize("scenario", MATRIX_SCENARIOS)
def test_kennel_matrix_atlas_matches_reference(scenario: str) -> None:
    """Each bundled scenario atlas matches shelter_planner_sim for placements and transfers."""
    wipe_state()
    run_pipeline(scenario)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_atlas(FIXTURE_ROOT, scenario)
    assert atlas["placements"] == ref["placements"]
    assert atlas["transfers"] == ref["transfers"]


def test_kennel_matrix_engine_field() -> None:
    """Published /app/output/placement-atlas.json includes engine intakectl."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert atlas.get("engine") == "intakectl"
