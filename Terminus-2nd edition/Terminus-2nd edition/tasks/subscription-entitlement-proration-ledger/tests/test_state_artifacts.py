"""Contract probes for entitlement buffer and SQLite persistence."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from cycle_harness import (
    DB_PATH,
    INVOICE_JSON,
    drive_billing_cycle,
    reset_billing_workspace,
)

RECONCILE_PASS = Path("/app/state/reconcile-pass.json")


def test_contract_billing_db_path_contract() -> None:
    """load-cycle must persist catalog rows at /app/state/billing.db."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    assert DB_PATH.as_posix() == "/app/state/billing.db"
    assert DB_PATH.is_file()


def test_contract_reconcile_pass_json_path_contract() -> None:
    """reconcile-entitlements must advance /app/state/reconcile-pass.json."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    assert RECONCILE_PASS.as_posix() == "/app/state/reconcile-pass.json"
    body = json.loads(RECONCILE_PASS.read_text(encoding="utf-8"))
    assert body["reconcile_pass"] >= 1


def test_contract_subscription_invoices_output_path() -> None:
    """publish-invoices must write /app/output/subscription-invoices.json."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    assert INVOICE_JSON.as_posix() == "/app/output/subscription-invoices.json"
    assert INVOICE_JSON.is_file()


def test_contract_segments_persisted_in_sqlite() -> None:
    """Mid-cycle upgrade must persist multiple entitlement segments in billing.db."""
    reset_billing_workspace()
    drive_billing_cycle("mid-upgrade")
    con = sqlite3.connect(DB_PATH)
    try:
        n = con.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
    finally:
        con.close()
    assert n >= 2


def test_contract_meta_scenario_id_roundtrip() -> None:
    """meta.scenario_id in billing.db must match ingested scenario slug."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    con = sqlite3.connect(DB_PATH)
    try:
        sid = con.execute("SELECT value FROM meta WHERE key='scenario_id'").fetchone()[0]
    finally:
        con.close()
    assert sid == "clean-monthly"


def test_contract_ledger_rows_appended_on_reconcile() -> None:
    """reconcile-entitlements must append ledger rows during entitlement pass."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    con = sqlite3.connect(DB_PATH)
    try:
        n = con.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
    finally:
        con.close()
    assert n >= 1
