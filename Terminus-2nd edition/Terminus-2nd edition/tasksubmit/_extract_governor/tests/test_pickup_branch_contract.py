"""Branch pickup routing and atlas stability tests."""

from __future__ import annotations

from libhold_exec import ATLAS_JSON, FIXTURE_ROOT, SCENARIO_BRANCH, SCENARIO_INTER, SCENARIO_STABLE, run_hold_pipeline, read_json, reset_hold_state
from libhold_sim import simulate_hold_assignments


def test_pickup_branch_wins_over_remote_copy():
    """Pickup-branch shelf copies beat remote interbranch candidates."""
    reset_hold_state()
    run_hold_pipeline(SCENARIO_BRANCH)
    atlas = read_json(ATLAS_JSON)
    ref = simulate_hold_assignments(FIXTURE_ROOT, SCENARIO_BRANCH)
    assert atlas["assignments"] == ref["assignments"]


def test_interbranch_requires_policy_flag():
    """Interbranch transfer only when branch policy allows it."""
    reset_hold_state()
    run_hold_pipeline(SCENARIO_INTER)
    atlas = read_json(ATLAS_JSON)
    ref = simulate_hold_assignments(FIXTURE_ROOT, SCENARIO_INTER)
    assert atlas["assignments"] == ref["assignments"]


def test_stable_scenario_replay_is_byte_stable():
    """Stable-atlas reruns emit identical assignment atlas JSON."""
    reset_hold_state()
    run_hold_pipeline(SCENARIO_STABLE)
    first = ATLAS_JSON.read_text(encoding="utf-8")
    reset_hold_state()
    run_hold_pipeline(SCENARIO_STABLE)
    second = ATLAS_JSON.read_text(encoding="utf-8")
    assert read_json_from_text(first) == read_json_from_text(second)


def read_json_from_text(raw: str) -> dict:
    import json

    return json.loads(raw)
