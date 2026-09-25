"""ETHSR adjacency orphan guard and accessibility inventory floor probes."""

from __future__ import annotations

import json
import sqlite3

from ethsr_driver import (
    CONFLICT_JSON,
    FIXTURE_ROOT,
    SCENARIO_ADJACENCY,
    SCENARIO_A11Y,
    SQLITE_OUT,
    drive_ethsr_pipeline,
    fetch_sqlite_seat_rows,
    wipe_state,
)
from venue_hold_simulator import simulate_hold_ledger


def test_ethsr_M01_adjacency_conflict_codes():
    """Adjacency-block-contract: orphan seats surface in hold-conflict-atlas.json."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_ADJACENCY)
    ref = simulate_hold_ledger(FIXTURE_ROOT, SCENARIO_ADJACENCY)
    report = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    assert report["conflicts"] == ref["conflicts"]


def test_ethsr_M02_adjacency_clean_assignments():
    """Adjacency-block-contract: valid rows land in venue-seat-ledger.sqlite."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_ADJACENCY)
    ref = simulate_hold_ledger(FIXTURE_ROOT, SCENARIO_ADJACENCY)
    assert fetch_sqlite_seat_rows() == ref["assignments"]


def test_ethsr_M03_a11y_inventory_conflicts():
    """A11y-inventory-contract: accessibility floor breaches appear in conflict atlas."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_A11Y)
    ref = simulate_hold_ledger(FIXTURE_ROOT, SCENARIO_A11Y)
    report = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    assert report["conflicts"] == ref["conflicts"]


def test_ethsr_M04_a11y_non_accessible_assignments():
    """A11y-inventory-contract: non-accessible seats still assign to venue-seat-ledger.sqlite."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_A11Y)
    ref = simulate_hold_ledger(FIXTURE_ROOT, SCENARIO_A11Y)
    assert fetch_sqlite_seat_rows() == ref["assignments"]


def test_ethsr_M05_sqlite_schema_columns():
    """Venue-ledger-contract: venue-seat-ledger.sqlite exposes seat_status and reconcile_meta columns."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_ADJACENCY)
    conn = sqlite3.connect(SQLITE_OUT)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(seat_status)").fetchall()]
    meta_cols = [r[1] for r in conn.execute("PRAGMA table_info(reconcile_meta)").fetchall()]
    conn.close()
    assert cols == ["seat_id", "hold_id", "order_id", "status"]
    assert meta_cols == ["scenario", "run_stamp", "map_pass_count"]
