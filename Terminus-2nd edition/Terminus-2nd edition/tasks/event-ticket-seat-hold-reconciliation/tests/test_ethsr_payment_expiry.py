"""ETHSR payment capture rank and hold expiry contract probes."""

from __future__ import annotations

import json

from ethsr_driver import (
    CONFLICT_JSON,
    FIXTURE_ROOT,
    SCENARIO_EXPIRY,
    SCENARIO_MULTI,
    SCENARIO_PAYMENT,
    SCENARIO_STABLE,
    drive_ethsr_pipeline,
    fetch_sqlite_seat_rows,
    wipe_state,
)
from venue_hold_simulator import simulate_hold_ledger


def test_ethsr_P01_lower_payment_rank_captures_seat():
    """Payment-precedence-contract: lower payment_rank wins seat capture in venue-seat-ledger.sqlite."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_PAYMENT)
    ref = simulate_hold_ledger(FIXTURE_ROOT, SCENARIO_PAYMENT)
    rows = fetch_sqlite_seat_rows()
    assert rows == ref["assignments"]
    assert len(rows) >= 1


def test_ethsr_P02_conflict_severity_order_locked():
    """Payment-precedence-contract: conflict precedence matches hold-conflict-atlas.json reference."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_PAYMENT)
    report = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    ref = simulate_hold_ledger(FIXTURE_ROOT, SCENARIO_PAYMENT)
    assert report["conflicts"] == ref["conflicts"]


def test_ethsr_P03_expired_hold_skipped():
    """Hold-expiry-contract: expired holds are omitted from venue-seat-ledger.sqlite."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_EXPIRY)
    ref = simulate_hold_ledger(FIXTURE_ROOT, SCENARIO_EXPIRY)
    assert fetch_sqlite_seat_rows() == ref["assignments"]


def test_ethsr_P04_multi_section_coverage():
    """Scenario-sqlite-contract: multi-section bundles assign seats across sections."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_MULTI)
    ref = simulate_hold_ledger(FIXTURE_ROOT, SCENARIO_MULTI)
    rows = fetch_sqlite_seat_rows()
    assert rows == ref["assignments"]
    assert len({r["seat_id"] for r in rows}) >= 2


def test_ethsr_P05_stable_ledger_byte_repeatable():
    """Repeat-run contract: repeated pipeline yields identical venue-seat-ledger.sqlite rows."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_STABLE)
    first = fetch_sqlite_seat_rows()
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_STABLE)
    second = fetch_sqlite_seat_rows()
    assert first == second
