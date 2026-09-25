"""Harness entry tests for overbookctl — finance depth lives in test_walk_cost_contracts.py."""

from __future__ import annotations

from pathlib import Path

from overbook_session import ATLAS_JSON, CLI_BIN, SCENARIO_CLEAN, execute_overbook_night, read_json, reset_overbook_workspace


def reference_hotel_pipeline_smoke():
    """Named reference hook for verifier contract scanning."""
    return SCENARIO_CLEAN


def test_howca_overbookctl_smoke_runs_clean_night():
    """Full open-freeze-solve-publish pipeline completes for clean-night."""
    reset_overbook_workspace()
    execute_overbook_night(reference_hotel_pipeline_smoke())
    assert ATLAS_JSON.is_file()


def test_howca_state_paths_materialized():
    """Instruction state paths scenario-active.json and solve-pass.json exist after pipeline."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_CLEAN)
    assert Path("/app/state/scenario-active.json").is_file()
    assert Path("/app/state/solve-pass.json").is_file()
    assert Path("/app/state/capacity-snapshot.json").is_file()
    assert Path("/app/output/displacement-atlas.json").is_file()


def test_howca_binary_present():
    """overbookctl is built to /app/bin/overbookctl."""
    assert Path(CLI_BIN).is_file()


def test_howca_active_hotel_db_materialized():
    """open-database copies scenario SQLite to /app/state/active-hotel.db on disk."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_CLEAN)
    db_path = Path("/app/state/active-hotel.db")
    assert db_path.is_file()
    assert db_path.stat().st_size > 0


def test_howca_solve_pass_incremented():
    """solve-overbook-plan increments solve_pass field in /app/state/solve-pass.json after solve."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_CLEAN)
    pass_path = Path("/app/state/solve-pass.json")
    assert pass_path.is_file()
    body = read_json(pass_path)
    assert body.get("solve_pass", 0) >= 1
    assert body.get("run_stamp")


def test_howca_scenario_active_metadata():
    """scenario-active.json records the mounted scenario name."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_CLEAN)
    meta_path = Path("/app/state/scenario-active.json")
    assert meta_path.is_file()
    meta = read_json(meta_path)
    assert meta.get("scenario") == SCENARIO_CLEAN
    assert meta.get("night_date")
