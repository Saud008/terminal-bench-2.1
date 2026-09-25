"""Smoke and bundled settlement scenarios."""

from __future__ import annotations

import json
import sqlite3
import subprocess

from auct_runner import (
    AUCT_BIN,
    DB_PATH,
    FIXTURE_ROOT,
    INVOICE_JSON,
    invoke,
    run_pipeline,
    wipe_state,
)
from auction_refmath import reference_awards, reference_invoices


def test_t4db0b2_abl_smoke_load_creates_sqlite_catalog() -> None:
    """load-catalog must create /app/state/settlement.db with catalog rows."""
    wipe_state()
    proc = subprocess.run(
        [
            AUCT_BIN,
            "load-catalog",
            "--scenario",
            "clean-award",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert DB_PATH.as_posix() == "/app/state/settlement.db"
    assert DB_PATH.is_file()
    con = sqlite3.connect(DB_PATH)
    try:
        lots = con.execute("SELECT COUNT(*) FROM lots").fetchone()[0]
        bids = con.execute("SELECT COUNT(*) FROM bids").fetchone()[0]
    finally:
        con.close()
    assert lots == 1
    assert bids == 1


def test_t4db0b2_abl_clean_award_invoice_matches_reference() -> None:
    """clean-award invoices must match independent reference math."""
    wipe_state()
    run_pipeline("clean-award")
    assert INVOICE_JSON.as_posix() == "/app/output/buyer-invoices.json"
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    ref = reference_invoices("clean-award", FIXTURE_ROOT)
    assert body["invoices"] == ref["invoices"]
    assert body["ledger_digest"] == ref["ledger_digest"]


def test_t4db0b2_abl_reserve_equal_meets_floor() -> None:
    """Hammer equal to reserve_cents must award per reserve-enforcement-contract."""
    wipe_state()
    run_pipeline("reserve-equal")
    ref = reference_invoices("reserve-equal", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]


def test_t4db0b2_abl_reserve_pass_no_invoice_rows() -> None:
    """Below-reserve lots produce empty invoices array at /app/output/buyer-invoices.json."""
    wipe_state()
    run_pipeline("reserve-pass")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == []


def test_t4db0b2_abl_tie_break_earlier_ts_wins() -> None:
    """Equal hammer must pick earlier bid_ts per tie-break-contract."""
    wipe_state()
    run_pipeline("tie-break-ts")
    ref = reference_invoices("tie-break-ts", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]


def test_t4db0b2_abl_tie_break_lower_bidder_id_wins() -> None:
    """Equal hammer and bid_ts must pick lower bidder_id."""
    wipe_state()
    run_pipeline("tie-break-bidder")
    ref = reference_invoices("tie-break-bidder", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]


def test_t4db0b2_abl_withdrawn_lot_suppresses_award() -> None:
    """Withdrawn lots must not appear in buyer invoices."""
    wipe_state()
    run_pipeline("withdrawn-lot")
    awards = reference_awards("withdrawn-lot", FIXTURE_ROOT)
    assert awards[0]["status"] == "withdrawn"
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == []


def test_t4db0b2_abl_deposit_netting_reduces_due() -> None:
    """Deposits reduce amount_due_cents per deposit-application-contract."""
    wipe_state()
    run_pipeline("deposit-netting")
    ref = reference_invoices("deposit-netting", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]


def test_t4db0b2_abl_premium_tier_luxury_cap() -> None:
    """Luxury premium_tier applies rate_bps cap from premium-schedule-contract."""
    wipe_state()
    run_pipeline("premium-tier")
    ref = reference_invoices("premium-tier", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]


def test_t4db0b2_abl_post_sale_negative_adjustment() -> None:
    """Negative adjustment_cents must remain signed in invoices."""
    wipe_state()
    run_pipeline("post-sale-adjust")
    ref = reference_invoices("post-sale-adjust", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]


def test_t4db0b2_abl_multi_lot_shared_deposit_order() -> None:
    """Shared deposit applies across sorted lot invoice order."""
    wipe_state()
    run_pipeline("multi-lot-shared-deposit")
    ref = reference_invoices("multi-lot-shared-deposit", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]


def test_t4db0b2_abl_adjudication_pass_increments() -> None:
    """adjudicate-lots must bump /app/state/adjudication-pass.json."""
    wipe_state()
    run_pipeline("clean-award")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["adjudication_pass"] == 1


def test_t4db0b2_abl_adjudication_pass_json_path() -> None:
    """adjudication-pass.json lives under /app/state with integer pass counter."""
    wipe_state()
    run_pipeline("clean-award")
    from auct_runner import PASS_JSON

    body = json.loads(PASS_JSON.read_text(encoding="utf-8"))
    assert PASS_JSON.as_posix() == "/app/state/adjudication-pass.json"
    assert body["adjudication_pass"] == 1


def test_t4db0b2_abl_buffer_awards_row_count() -> None:
    """Awards buffer table must hold awarded rows after adjudicate-lots."""
    wipe_state()
    run_pipeline("clean-award")
    con = sqlite3.connect(DB_PATH)
    try:
        n = con.execute("SELECT COUNT(*) FROM awards WHERE status='awarded'").fetchone()[0]
    finally:
        con.close()
    assert n == 1


def test_t4db0b2_abl_publish_requires_positive_pass() -> None:
    """publish-invoices rejects when adjudication_pass is zero."""
    wipe_state()
    invoke(
        [
            AUCT_BIN,
            "load-catalog",
            "--scenario",
            "clean-award",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    proc = invoke([AUCT_BIN, "publish-invoices", "--scenario", "clean-award"])
    assert proc.returncode != 0


def test_t4db0b2_abl_invoice_sorted_by_lot_then_bidder() -> None:
    """Invoice rows sorted by lot_id then bidder_id."""
    wipe_state()
    run_pipeline("multi-lot-shared-deposit")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    lots = [row["lot_id"] for row in body["invoices"]]
    assert lots == sorted(lots)
