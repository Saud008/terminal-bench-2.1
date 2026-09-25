"""Patron suspension calendar and priority tier contract tests."""

from __future__ import annotations

from libhold_exec import (
    ATLAS_JSON,
    FIXTURE_ROOT,
    SCENARIO_MULTI,
    SCENARIO_SUSPEND,
    SCENARIO_TIER,
    read_json,
    reset_hold_state,
    run_hold_pipeline,
)
from libhold_sim import simulate_hold_assignments


def test_calendar_block_excludes_suspended_patron():
    """Active suspension windows exclude the patron from new assignments."""
    reset_hold_state()
    run_hold_pipeline(SCENARIO_SUSPEND)
    atlas = read_json(ATLAS_JSON)
    ref = simulate_hold_assignments(FIXTURE_ROOT, SCENARIO_SUSPEND)
    assert atlas["assignments"] == ref["assignments"]


def test_teacher_tier_wins_over_standard_hold():
    """Lower priority-class rank wins the single available copy."""
    reset_hold_state()
    run_hold_pipeline(SCENARIO_TIER)
    atlas = read_json(ATLAS_JSON)
    ref = simulate_hold_assignments(FIXTURE_ROOT, SCENARIO_TIER)
    assert atlas["assignments"] == ref["assignments"]
    assert len(atlas["assignments"]) == 1


def test_multi_item_scenario_yields_two_rows():
    """Multi-hold fixtures emit at least two assignment rows."""
    reset_hold_state()
    run_hold_pipeline(SCENARIO_MULTI)
    atlas = read_json(ATLAS_JSON)
    ref = simulate_hold_assignments(FIXTURE_ROOT, SCENARIO_MULTI)
    assert atlas["assignments"] == ref["assignments"]
    assert len(atlas["assignments"]) >= 2
