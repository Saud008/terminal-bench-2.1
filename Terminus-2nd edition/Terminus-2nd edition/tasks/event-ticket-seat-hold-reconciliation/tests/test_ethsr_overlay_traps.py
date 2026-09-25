"""ETHSR TB3 overlay traps: expiry boundary and accessibility hidden scenarios."""

from __future__ import annotations

import json
import os

from ethsr_driver import (
    CONFLICT_JSON,
    HIDDEN_ROOT,
    drive_ethsr_pipeline,
    fetch_sqlite_seat_rows,
    wipe_state,
)
from venue_hold_simulator import simulate_hold_ledger


def test_ethsr_T01_hidden_expiry_boundary():
    """Hold-expiry-contract: inclusive expires_at boundary under TB3_EVENT_CLOCK overlay."""
    scenario = "expiry-boundary-trap"
    wipe_state()
    drive_ethsr_pipeline(
        scenario,
        fixture_root=HIDDEN_ROOT,
        extra_env={"TB3_EVENT_CLOCK": "2026-04-05T12:00:00Z"},
    )
    ref = simulate_hold_ledger(HIDDEN_ROOT, scenario)
    assert fetch_sqlite_seat_rows() == ref["assignments"]


def test_ethsr_T02_hidden_a11y_trap_conflicts():
    """A11y-inventory-contract: hidden overlay scenario conflicts match reference math."""
    scenario = "a11y-hidden-trap"
    wipe_state()
    drive_ethsr_pipeline(scenario, fixture_root=HIDDEN_ROOT)
    ref = simulate_hold_ledger(HIDDEN_ROOT, scenario)
    report = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    assert report["conflicts"] == ref["conflicts"]


def test_ethsr_T03_event_clock_env_override():
    """CLI surface: TB3_EVENT_CLOCK replaces scenario event clock for overlay runs."""
    scenario = "expiry-boundary-trap"
    wipe_state()
    os.environ["TB3_EVENT_CLOCK"] = "2026-04-05T12:00:00Z"
    try:
        drive_ethsr_pipeline(scenario, fixture_root=HIDDEN_ROOT)
        ref = simulate_hold_ledger(HIDDEN_ROOT, scenario)
        assert fetch_sqlite_seat_rows() == ref["assignments"]
    finally:
        os.environ.pop("TB3_EVENT_CLOCK", None)


def test_ethsr_T04_fixture_dir_redirect():
    """CLI surface: TB3_FIXTURE_DIR redirects bundled roots to verifier overlay fixtures."""
    scenario = "a11y-hidden-trap"
    wipe_state()
    drive_ethsr_pipeline(
        scenario,
        fixture_root=HIDDEN_ROOT,
        extra_env={"TB3_FIXTURE_DIR": str(HIDDEN_ROOT)},
    )
    ref = simulate_hold_ledger(HIDDEN_ROOT, scenario)
    assert fetch_sqlite_seat_rows() == ref["assignments"]
