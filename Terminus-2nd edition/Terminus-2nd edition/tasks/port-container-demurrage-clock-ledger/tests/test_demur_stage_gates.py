"""PCDL stage gate tests: CLI surface, clock_pass, and staging prerequisites."""

from __future__ import annotations

import json
from pathlib import Path

from demur_harness import (
    CLI_BIN,
    FIXTURE_ROOT,
    SCENARIO_BASIC,
    SCENARIO_CLOSURE,
    SCENARIO_HOLD,
    SCENARIO_DWELL_GATE,
    LEDGER_JSON,
    drive_demur_pipeline,
    invoke,
    read_clock_pass,
    wipe_state,
)
from demur_refmath import reference_invoices


def test_demur_S01_binary_on_path():
    """CLI surface: demurctl binary is installed at /app/bin/demurctl."""
    assert Path(CLI_BIN).is_file()


def test_demur_S02_missing_subcommand_nonzero():
    """CLI surface: invoking demurctl without a subcommand exits non-zero."""
    proc = invoke([str(CLI_BIN)])
    assert proc.returncode != 0


def test_demur_S03_publish_blocked_before_staging():
    """Invoice-publish-contract: publish-invoices fails when clock_pass is zero."""
    wipe_state()
    proc = invoke(
        [
            str(CLI_BIN),
            "load-yard",
            "--scenario",
            SCENARIO_DWELL_GATE,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    proc = invoke([str(CLI_BIN), "publish-invoices"])
    assert proc.returncode != 0


def test_demur_S04_clock_pass_increments_on_staging():
    """Dwell-ledger-contract: run-dwell-ledger increments clock_pass."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_DWELL_GATE)
    assert read_clock_pass() == 1
    invoke([str(CLI_BIN), "run-dwell-ledger"])
    assert read_clock_pass() == 2


def test_demur_S05_staging_gate_scenario():
    """Dwell-ledger-contract: daemon rollout dwell-gate writes dwell-ledger manifest."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_DWELL_GATE)
    assert LEDGER_JSON.is_file()
    body = json.loads(LEDGER_JSON.read_text(encoding="utf-8"))
    assert body["engine"] == "demurctl"
    assert body["clock_pass"] == 1


def test_demur_S06_basic_free_time_invoices():
    """Free-time-clock-contract: basic-free-time invoice lines match reference math."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_BASIC)
    ref = reference_invoices(FIXTURE_ROOT, SCENARIO_BASIC)
    report = json.loads(Path("/app/output/demurrage-invoices.json").read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]
    assert report["grand_total_cents"] == ref["grand_total_cents"]


def test_demur_S07_hold_pause_customs():
    """Hold-precedence-contract: customs hold pause changes eligible days vs reference."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_HOLD)
    ref = reference_invoices(FIXTURE_ROOT, SCENARIO_HOLD)
    report = json.loads(Path("/app/output/demurrage-invoices.json").read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]


def test_demur_S08_closure_skip():
    """Closure-calendar-contract: closure-skip scenario totals match reference math."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_CLOSURE)
    ref = reference_invoices(FIXTURE_ROOT, SCENARIO_CLOSURE)
    report = json.loads(Path("/app/output/demurrage-invoices.json").read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]
