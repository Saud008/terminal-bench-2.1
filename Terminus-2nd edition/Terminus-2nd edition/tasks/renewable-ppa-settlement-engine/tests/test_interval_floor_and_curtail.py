"""Bundled PPA settlement contract scenarios against independent reference math."""

from __future__ import annotations

import json
import sqlite3

from ppa_ctl_exec import (
    DB_PATH,
    FIXTURE_ROOT,
    INVOICE_PATH,
    JSONL_PATH,
    drive_settlement,
    reset_ppa_workspace,
    run_export_invoice_rollup,
    run_ingest_materialize_lines,
)
from ppa_settlement_math import reference_invoice, reference_lines


def _read_lines() -> list[dict]:
    return [json.loads(row) for row in JSONL_PATH.read_text(encoding="utf-8").splitlines() if row.strip()]


def test_curtailment_skip_flags_skipped_line() -> None:
    """Curtailment mask must mark intervals inside half-open windows as skipped_curtail."""
    reset_ppa_workspace()
    drive_settlement("curtailment-skip")
    lines = _read_lines()
    assert len(lines) == 1
    assert lines[0]["skipped_curtail"] is True


def test_curtailment_skip_zero_settlement_amount() -> None:
    """Curtailed intervals must settle to zero cents per curtailment-mask-contract."""
    reset_ppa_workspace()
    drive_settlement("curtailment-skip")
    ref = reference_lines("curtailment-skip", FIXTURE_ROOT)
    assert _read_lines() == ref
    assert ref[0]["amount_cents"] == 0


def test_strike_floor_uses_max_market_price() -> None:
    """Numeric closure tolerance: strike settlement must use max(strike, market) per contract."""
    reset_ppa_workspace()
    drive_settlement("strike-floor")
    line = _read_lines()[0]
    assert line["settlement_cents"] == 5200
    assert line["amount_cents"] == 5200


def test_strike_floor_invoice_total_matches_reference() -> None:
    """Strike-floor invoice total must match independent reference rollup."""
    reset_ppa_workspace()
    drive_settlement("strike-floor")
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    ref = reference_invoice("strike-floor", FIXTURE_ROOT)
    assert body["total_amount_cents"] == ref["total_amount_cents"]


def test_holiday_trim_billing_days_excludes_in_period_holiday() -> None:
    """Holiday rollup must exclude in-period ISO holidays from billing_days."""
    reset_ppa_workspace()
    drive_settlement("holiday-trim")
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    assert body["billing_days"] == 6


def test_holiday_trim_invoice_matches_reference() -> None:
    """Holiday-trim billing_days must match reference holiday-rollup-contract math."""
    reset_ppa_workspace()
    drive_settlement("holiday-trim")
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    ref = reference_invoice("holiday-trim", FIXTURE_ROOT)
    assert body["billing_days"] == ref["billing_days"]


def test_multi_meter_emits_two_settlement_lines() -> None:
    """Multi-meter scenarios must emit one settlement line per meter interval."""
    reset_ppa_workspace()
    drive_settlement("multi-meter")
    lines = _read_lines()
    assert len(lines) == 2
    meter_ids = {line["meter_id"] for line in lines}
    assert meter_ids == {"M-A", "M-B"}


def test_multi_meter_shared_interval_alignment() -> None:
    """All meters must share the same UTC interval floor after alignment."""
    reset_ppa_workspace()
    drive_settlement("multi-meter")
    lines = _read_lines()
    assert all(line["interval_start_utc"] == "2026-01-05T06:00:00Z" for line in lines)


def test_multi_meter_invoice_total_matches_reference() -> None:
    """Multi-meter invoice total must equal independent reference sum."""
    reset_ppa_workspace()
    drive_settlement("multi-meter")
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    ref = reference_invoice("multi-meter", FIXTURE_ROOT)
    assert body["total_amount_cents"] == ref["total_amount_cents"]


def test_multi_meter_lines_match_reference() -> None:
    """Multi-meter JSONL lines must match ppa_settlement_math line-for-line."""
    reset_ppa_workspace()
    drive_settlement("multi-meter")
    assert _read_lines() == reference_lines("multi-meter", FIXTURE_ROOT)


def test_republish_stable_lines_digest_constant() -> None:
    """Republish-stable must yield identical lines_digest across repeated runs."""
    reset_ppa_workspace()
    drive_settlement("republish-stable")
    first = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))["lines_digest"]
    drive_settlement("republish-stable")
    second = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))["lines_digest"]
    assert first == second


def test_republish_stable_invoice_matches_reference() -> None:
    """Republish-stable invoice must match reference digest and totals."""
    reset_ppa_workspace()
    drive_settlement("republish-stable")
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    ref = reference_invoice("republish-stable", FIXTURE_ROOT)
    assert body == ref


def test_interval_align_floors_reading_to_lower_boundary() -> None:
    """Lab calibration floors meter readings to the lower fifteen-minute UTC boundary."""
    reset_ppa_workspace()
    drive_settlement("clean-interval")
    line = _read_lines()[0]
    assert line["interval_start_utc"] == "2026-01-02T12:00:00Z"


def test_sqlite_meta_records_scenario_id() -> None:
    """SQLite meta table at /app/state/ppa-settlement.db must record scenario_id."""
    reset_ppa_workspace()
    drive_settlement("clean-interval")
    assert DB_PATH.as_posix() == "/app/state/ppa-settlement.db"
    con = sqlite3.connect(DB_PATH)
    try:
        scenario = con.execute("SELECT value FROM meta WHERE key='scenario_id'").fetchone()[0]
    finally:
        con.close()
    assert scenario == "clean-interval"


def test_sqlite_settlement_rows_match_jsonl_amounts() -> None:
    """SQLite settlement_lines rows must mirror JSONL amount_cents per line."""
    reset_ppa_workspace()
    drive_settlement("clean-interval")
    lines = _read_lines()
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute(
            "SELECT meter_id, amount_cents, skipped_curtail FROM settlement_lines ORDER BY id"
        ).fetchall()
    finally:
        con.close()
    assert rows[0][0] == lines[0]["meter_id"]
    assert rows[0][1] == lines[0]["amount_cents"]


def test_invoice_line_count_excludes_curtailed_rows() -> None:
    """Invoice line_count must exclude curtailed rows from rollup totals."""
    reset_ppa_workspace()
    drive_settlement("curtailment-skip")
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    assert body["line_count"] == 0
    assert body["total_amount_cents"] == 0


def test_jsonl_schema_contains_settlement_fields() -> None:
    """Each JSONL row must expose settlement schema fields from rollup-json-schema."""
    reset_ppa_workspace()
    drive_settlement("strike-floor")
    line = _read_lines()[0]
    for key in (
        "meter_id",
        "interval_start_utc",
        "mwh",
        "strike_cents",
        "market_cents",
        "settlement_cents",
        "amount_cents",
        "skipped_curtail",
    ):
        assert key in line


def test_clean_interval_strike_wins_when_market_lower() -> None:
    """When market is below strike, settlement must use strike cents per MWh."""
    reset_ppa_workspace()
    drive_settlement("clean-interval")
    line = _read_lines()[0]
    assert line["settlement_cents"] == 4500
    assert line["amount_cents"] == 6750


def test_ingest_staging_snapshot_written_before_export() -> None:
    """Ingest materialize-lines must write a staging snapshot JSONL before export rollup."""
    reset_ppa_workspace()
    run_ingest_materialize_lines("clean-interval")
    assert JSONL_PATH.is_file()
    staging_snapshot = [json.loads(row) for row in JSONL_PATH.read_text(encoding="utf-8").splitlines() if row.strip()]
    assert len(staging_snapshot) == 1
    assert staging_snapshot[0]["meter_id"] == "M-SOL-A"


def test_export_only_rollup_reads_staging_lines() -> None:
    """Export rollup-billing-invoice must read staged lines and emit invoice JSON."""
    reset_ppa_workspace()
    run_ingest_materialize_lines("strike-floor")
    assert JSONL_PATH.is_file()
    run_export_invoice_rollup("strike-floor")
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    ref = reference_invoice("strike-floor", FIXTURE_ROOT)
    assert body["total_amount_cents"] == ref["total_amount_cents"]


def test_ingest_only_does_not_publish_invoice_export() -> None:
    """Ingest-only materialize must not create export invoice until rollup runs."""
    reset_ppa_workspace()
    run_ingest_materialize_lines("holiday-trim")
    assert JSONL_PATH.is_file()
    assert not INVOICE_PATH.exists()
