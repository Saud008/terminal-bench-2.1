"""Verifier-only TB3 traps for maintenance boundary and hidden walk-cost tables."""

from __future__ import annotations

from hotel_finance_sim import simulate_capacity_snapshot, simulate_displacement_atlas
from overbook_session import HIDDEN_ROOT, ATLAS_JSON, SNAPSHOT_JSON, execute_overbook_night, read_json, reset_overbook_workspace


def reference_hotel_capacity_snapshot(fixture_root, scenario):
    return simulate_capacity_snapshot(fixture_root, scenario)


def reference_hotel_displacement_atlas(fixture_root, scenario):
    return simulate_displacement_atlas(fixture_root, scenario)


def test_hrev_tb3_maintenance_inclusive_end():
    """Hidden maintenance-boundary-trap requires inclusive end_date blackout on TB3_NIGHT_DATE."""
    scenario = "maintenance-boundary-trap"
    reset_overbook_workspace()
    execute_overbook_night(
        scenario,
        fixture_root=HIDDEN_ROOT,
        extra_env={"TB3_NIGHT_DATE": "2026-04-05"},
    )
    staging = read_json(SNAPSHOT_JSON)
    ref_staging = reference_hotel_capacity_snapshot(HIDDEN_ROOT, scenario)
    assert staging["capacity_fingerprint"] == ref_staging["capacity_fingerprint"]
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(HIDDEN_ROOT, scenario)
    assert atlas["assignments"] == ref["assignments"]


def test_hrev_tb3_hidden_walk_cost_table():
    """Hidden walk-cost-hidden-trap uses verifier-only walk_cost rows for displacement ties."""
    scenario = "walk-cost-hidden-trap"
    reset_overbook_workspace()
    execute_overbook_night(scenario, fixture_root=HIDDEN_ROOT)
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(HIDDEN_ROOT, scenario)
    assert atlas["walks"] == ref["walks"]
    assert atlas["walks"][0]["to_type_id"] == ref["walks"][0]["to_type_id"]
