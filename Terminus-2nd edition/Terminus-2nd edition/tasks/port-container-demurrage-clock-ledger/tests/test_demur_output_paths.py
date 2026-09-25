"""PCDL output path and invoice contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from demur_harness import (
    CLI_BIN,
    CLOCK_PASS,
    FIXTURE_ROOT,
    INVOICE_JSON,
    SCENARIO_BASIC,
    SCENARIO_IDEM,
    SCENARIO_MULTI,
    SCENARIO_PRECEDENCE,
    SCENARIO_TIER,
    YARD_DB,
    drive_demur_pipeline,
    fetch_staged_dwell_rows,
    invoke,
    read_clock_pass,
    wipe_state,
)
from demur_refmath import reference_invoices


def test_demur_O01_load_yard_paths():
    """Yard-sqlite-contract: load-yard creates yard.db under /app/state."""
    wipe_state()
    proc = invoke(
        [
            str(CLI_BIN),
            "load-yard",
            "--scenario",
            SCENARIO_MULTI,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert YARD_DB.is_file()


def test_demur_O02_staging_json_exists():
    """Dwell-ledger-contract: run-dwell-ledger materializes /app/work/dwell-ledger.json."""
    wipe_state()
    invoke(
        [
            str(CLI_BIN),
            "load-yard",
            "--scenario",
            SCENARIO_TIER,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    proc = invoke([str(CLI_BIN), "run-dwell-ledger"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert Path("/app/work/dwell-ledger.json").is_file()


def test_demur_O03_invoice_json_exists():
    """Invoice-publish-contract: fleet demurrage invoice manifest at demurrage-invoices.json."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_TIER)
    assert INVOICE_JSON.is_file()


def test_demur_O04_hold_precedence_label():
    """Hold-precedence-contract: overlapping holds report CUSTOMS active_hold label."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_PRECEDENCE)
    ref = reference_invoices(FIXTURE_ROOT, SCENARIO_PRECEDENCE)
    report = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]
    assert ref["lines"][0].get("active_hold") == "CUSTOMS"


def test_demur_O05_tier_escalation():
    """Tariff-tier-contract: tier-escalation tier buckets match reference math."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_TIER)
    ref = reference_invoices(FIXTURE_ROOT, SCENARIO_TIER)
    report = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]


def test_demur_O06_multi_container():
    """Free-time-clock-contract: multi-container scenario emits sorted invoice lines."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_MULTI)
    ref = reference_invoices(FIXTURE_ROOT, SCENARIO_MULTI)
    report = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]
    assert len(report["lines"]) == 2


def test_demur_O07_rerun_stable():
    """Dwell-ledger-contract: rerun-stable second pipeline leaves invoice lines stable."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_IDEM)
    first = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))["lines"]
    drive_demur_pipeline(SCENARIO_IDEM)
    second = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))["lines"]
    assert first == second


def test_demur_O08_staged_dwell_sqlite():
    """Yard-sqlite-contract: staged_dwell SQLite rows match reference invoice rows."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_BASIC)
    ref = reference_invoices(FIXTURE_ROOT, SCENARIO_BASIC)
    rows = fetch_staged_dwell_rows()
    assert len(rows) == len(ref["rows"])
    for row, expected in zip(rows, ref["rows"], strict=True):
        assert row["container_id"] == expected["container_id"]
        assert row["total_cents"] == expected["total_cents"]
        assert row["tier1_days"] == expected["tier1_days"]
        assert row["tier2_days"] == expected["tier2_days"]
        assert row["tier3_days"] == expected["tier3_days"]


def test_demur_O09_clock_pass_json_path():
    """Invoice-publish-contract: daemon rollout updates clock-pass.json fleet gate counter."""
    wipe_state()
    invoke(
        [
            str(CLI_BIN),
            "load-yard",
            "--scenario",
            SCENARIO_BASIC,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    assert CLOCK_PASS.is_file()
    assert read_clock_pass() == 0
    proc = invoke([str(CLI_BIN), "run-dwell-ledger"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert CLOCK_PASS.as_posix() == "/app/state/clock-pass.json"
    assert read_clock_pass() == 1


def test_demur_O10_yard_db_absolute_path():
    """Yard-sqlite-contract: fleet topology config persists scenario tables at yard.db."""
    wipe_state()
    drive_demur_pipeline(SCENARIO_BASIC)
    assert YARD_DB.as_posix() == "/app/state/yard.db"
    assert YARD_DB.is_file()
