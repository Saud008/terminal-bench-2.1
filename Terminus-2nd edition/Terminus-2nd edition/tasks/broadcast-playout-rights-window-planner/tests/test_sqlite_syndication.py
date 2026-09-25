"""SQLite persistence and cross-run syndication recompile."""
from __future__ import annotations

import json
from pathlib import Path

from bcast_synd_refmath import reference_conflicts
from bcast_synd_cli import (
    CONFLICT_JSON,
    FIXTURE_ROOT,
    PLAN_JSON,
    SCENARIO_CLEAN,
    SCENARIO_IDEM,
    run_pipeline,
    sqlite_row_count,
    wipe_state,
)


def test_compile_epoch_counter_advances_each_pipeline():
    """Each compile-windows run must increment plan_pass in /app/state/compile-epoch.json."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    epoch_path = Path("/app/state/compile-epoch.json")
    assert epoch_path.is_file()
    first = json.loads(epoch_path.read_text(encoding="utf-8"))["plan_pass"]
    run_pipeline(SCENARIO_CLEAN)
    second = json.loads(epoch_path.read_text(encoding="utf-8"))["plan_pass"]
    assert second == first + 1


def test_sqlite_plan_rows_stable_after_second_compile():
    """Repeated compile-windows must not duplicate rows in /app/state/syndication-plan.db."""
    wipe_state()
    run_pipeline(SCENARIO_IDEM)
    assert Path("/app/state/syndication-plan.db").is_file()
    rows_after_first = sqlite_row_count(SCENARIO_IDEM)
    run_pipeline(SCENARIO_IDEM)
    rows_after_second = sqlite_row_count(SCENARIO_IDEM)
    assert rows_after_first == rows_after_second
    assert rows_after_first > 0


def test_syndication_and_conflict_bytes_unchanged_on_recompile():
    """Second pipeline run must yield byte-identical syndication-plan and conflict exports."""
    wipe_state()
    run_pipeline(SCENARIO_IDEM)
    plan_blob = PLAN_JSON.read_bytes()
    conflict_blob = CONFLICT_JSON.read_bytes()
    run_pipeline(SCENARIO_IDEM)
    assert PLAN_JSON.read_bytes() == plan_blob
    assert CONFLICT_JSON.read_bytes() == conflict_blob


def test_clean_scenario_exports_empty_conflict_ledger():
    """Clean playout must write /app/output/conflict-report.json with empty conflicts list."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    assert Path("/app/output/conflict-report.json").is_file()
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    report = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    expected = reference_conflicts(FIXTURE_ROOT, SCENARIO_CLEAN, plan["entries"])
    assert report["conflicts"] == expected
