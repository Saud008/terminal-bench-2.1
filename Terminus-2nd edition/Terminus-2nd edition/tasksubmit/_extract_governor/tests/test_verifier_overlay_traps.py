"""Alternate fixture-root and TB3_RECONCILE_DATE overlay checks."""

from __future__ import annotations

from libhold_exec import ATLAS_JSON, HIDDEN_ROOT, run_hold_pipeline, reset_hold_state, read_json
from libhold_sim import simulate_hold_assignments


def test_hidden_suspension_calendar_boundary():
    """TB3_RECONCILE_DATE keeps suspension boundary patrons blocked."""
    scenario = "suspension-boundary-trap"
    reset_hold_state()
    run_hold_pipeline(
        scenario,
        fixture_root=HIDDEN_ROOT,
        extra_env={"TB3_RECONCILE_DATE": "2026-03-02"},
    )
    atlas = read_json(ATLAS_JSON)
    ref = simulate_hold_assignments(HIDDEN_ROOT, scenario)
    assert atlas["assignments"] == ref["assignments"]


def test_hidden_branch_pickup_trap():
    """Overlay routing fixture still prefers pickup_branch_id copies."""
    scenario = "routing-hidden-trap"
    reset_hold_state()
    run_hold_pipeline(scenario, fixture_root=HIDDEN_ROOT)
    atlas = read_json(ATLAS_JSON)
    ref = simulate_hold_assignments(HIDDEN_ROOT, scenario)
    assert atlas["assignments"] == ref["assignments"]


def test_hidden_fixture_root_env_override():
    """Alternate fixture root under /opt remains mountable for overlays."""
    scenario = "suspension-boundary-trap"
    reset_hold_state()
    assert HIDDEN_ROOT.is_dir()
    run_hold_pipeline(
        scenario,
        fixture_root=HIDDEN_ROOT,
        extra_env={"TB3_RECONCILE_DATE": "2026-03-02"},
    )
    assert ATLAS_JSON.is_file()
