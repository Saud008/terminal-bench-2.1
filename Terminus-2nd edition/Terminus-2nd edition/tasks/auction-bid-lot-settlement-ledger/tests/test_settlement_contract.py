"""Contract probes — awards_buffer vs publish layers (catalog-stage partial fix fails hidden)."""

from __future__ import annotations

import json
import sqlite3

from auct_runner import AUCT_BIN, DB_PATH, FIXTURE_ROOT, INVOICE_JSON, invoke, wipe_state
from auction_refmath import reference_awards


def test_abl_staging_awards_buffer_snapshot_schema() -> None:
    """Staging snapshot: awards_buffer rows must match reference before publish export."""
    wipe_state()
    invoke(
        [
            AUCT_BIN,
            "load-catalog",
            "--scenario",
            "reserve-pass",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    invoke([AUCT_BIN, "adjudicate-lots", "--scenario", "reserve-pass"])
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute(
            "SELECT lot_id, status, hammer_cents FROM awards ORDER BY lot_id"
        ).fetchall()
    finally:
        con.close()
    ref = reference_awards("reserve-pass", FIXTURE_ROOT)
    snapshot = [
        {"lot_id": r[0], "status": r[1], "hammer_cents": r[2]} for r in rows
    ]
    expected = [
        {"lot_id": a["lot_id"], "status": a["status"], "hammer_cents": a["hammer_cents"]}
        for a in ref
    ]
    assert snapshot == expected


def test_abl_ingest_only_catalog_load_fails_publish_export() -> None:
    """Ingest-only catalog load without adjudication must block invoice export."""
    wipe_state()
    invoke(
        [
            AUCT_BIN,
            "load-catalog",
            "--scenario",
            "tie-break-ts",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    proc = invoke([AUCT_BIN, "publish-invoices", "--scenario", "tie-break-ts"])
    assert proc.returncode != 0


def test_abl_contract_awards_table_matches_reference() -> None:
    """SQLite awards must match reference adjudication output."""
    wipe_state()
    invoke(
        [
            AUCT_BIN,
            "load-catalog",
            "--scenario",
            "tie-break-ts",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    invoke([AUCT_BIN, "adjudicate-lots", "--scenario", "tie-break-ts"])
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute(
            "SELECT lot_id, status, bidder_id, hammer_cents FROM awards ORDER BY lot_id"
        ).fetchall()
    finally:
        con.close()
    ref = reference_awards("tie-break-ts", FIXTURE_ROOT)
    got = [
        {"lot_id": r[0], "status": r[1], "bidder_id": r[2] or "", "hammer_cents": r[3]}
        for r in rows
    ]
    assert got == ref


def test_abl_contract_withdrawn_status_in_buffer() -> None:
    """Withdrawn lots record withdrawn status in awards_buffer."""
    wipe_state()
    invoke(
        [
            AUCT_BIN,
            "load-catalog",
            "--scenario",
            "withdrawn-lot",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    invoke([AUCT_BIN, "adjudicate-lots", "--scenario", "withdrawn-lot"])
    con = sqlite3.connect(DB_PATH)
    try:
        status = con.execute("SELECT status FROM awards WHERE lot_id='L6'").fetchone()[0]
    finally:
        con.close()
    assert status == "withdrawn"


def test_abl_contract_idempotent_publish_same_digest() -> None:
    """Republish with same pass yields identical ledger_digest."""
    wipe_state()
    invoke(
        [
            AUCT_BIN,
            "load-catalog",
            "--scenario",
            "deposit-netting",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    invoke([AUCT_BIN, "adjudicate-lots", "--scenario", "deposit-netting"])
    invoke([AUCT_BIN, "publish-invoices", "--scenario", "deposit-netting"])
    first = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    invoke([AUCT_BIN, "publish-invoices", "--scenario", "deposit-netting"])
    second = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert first["ledger_digest"] == second["ledger_digest"]
    assert first["invoices"] == second["invoices"]


def test_abl_contract_deposit_applied_not_double_on_rerun() -> None:
    """Second publish must not double-apply deposits."""
    wipe_state()
    invoke(
        [
            AUCT_BIN,
            "load-catalog",
            "--scenario",
            "deposit-netting",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    invoke([AUCT_BIN, "adjudicate-lots", "--scenario", "deposit-netting"])
    invoke([AUCT_BIN, "publish-invoices", "--scenario", "deposit-netting"])
    invoke([AUCT_BIN, "publish-invoices", "--scenario", "deposit-netting"])
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"][0]["deposit_applied"] == 3000
