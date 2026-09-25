"""Bundled subscription entitlement proration scenarios.

Verifier contract: load-cycle ingest stage, entitlement-buffer staging snapshot digest,
and publish-invoices export isolation are independently probed.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess

from cycle_harness import (
    BUFFER_JSON,
    CTL_BIN,
    DB_PATH,
    FIXTURE_ROOT,
    INVOICE_JSON,
    drive_billing_cycle,
    reset_billing_workspace,
)
from entitlement_calc import reference_invoices, reference_staging


def test_proration_smoke_load_creates_billing_db() -> None:
    """load-cycle must create /app/state/billing.db with plan rows."""
    reset_billing_workspace()
    proc = subprocess.run(
        [
            CTL_BIN,
            "load-cycle",
            "--scenario",
            "clean-monthly",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert DB_PATH.is_file()
    con = sqlite3.connect(DB_PATH)
    try:
        plans = con.execute("SELECT COUNT(*) FROM plans").fetchone()[0]
    finally:
        con.close()
    assert plans >= 2


def test_proration_clean_monthly_invoice_matches_reference() -> None:
    """clean-monthly invoice lines must match entitlement_calc independent calculator."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    ref = reference_invoices("clean-monthly", FIXTURE_ROOT)
    assert body["invoice_lines"] == ref["invoice_lines"]
    assert body["ledger_digest"] == ref["ledger_digest"]


def test_proration_mid_upgrade_proration() -> None:
    """Mid-cycle upgrade must prorate base cents across two entitlement segments."""
    reset_billing_workspace()
    drive_billing_cycle("mid-upgrade")
    ref = reference_invoices("mid-upgrade", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"] == ref["invoice_lines"]


def test_proration_mid_downgrade_with_carryover() -> None:
    """Downgrade segments must apply usage carryover per usage-carryover-contract."""
    reset_billing_workspace()
    drive_billing_cycle("mid-downgrade")
    ref = reference_invoices("mid-downgrade", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"] == ref["invoice_lines"]


def test_proration_coupon_single_percent() -> None:
    """Single percent coupon must reduce subscription line per coupon-precedence-contract."""
    reset_billing_workspace()
    drive_billing_cycle("coupon-single")
    ref = reference_invoices("coupon-single", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"] == ref["invoice_lines"]


def test_proration_coupon_precedence_exclusive() -> None:
    """Exclusive coupons must pick largest discount only when both are non-stackable."""
    reset_billing_workspace()
    drive_billing_cycle("coupon-precedence")
    ref = reference_invoices("coupon-precedence", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"] == ref["invoice_lines"]


def test_proration_usage_carryover_on_downgrade() -> None:
    """Unused included units must carry into post-downgrade segment billing."""
    reset_billing_workspace()
    drive_billing_cycle("usage-carryover")
    ref = reference_invoices("usage-carryover", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"] == ref["invoice_lines"]


def test_proration_anchor_shift_truncates_window() -> None:
    """Anchor shift must truncate entitlement window per anchor-shift-contract."""
    reset_billing_workspace()
    drive_billing_cycle("anchor-shift")
    ref = reference_invoices("anchor-shift", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"] == ref["invoice_lines"]


def test_proration_multi_event_three_segments() -> None:
    """Two plan changes in one cycle must yield three invoice subscription lines."""
    reset_billing_workspace()
    drive_billing_cycle("multi-event")
    ref = reference_invoices("multi-event", FIXTURE_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert len(body["invoice_lines"]) == len(ref["invoice_lines"])
    assert body["invoice_lines"] == ref["invoice_lines"]


def test_proration_buffer_staging_snapshot_digest() -> None:
    """entitlement-buffer staging snapshot digest must match compact segments per entitlement-buffer-contract."""
    reset_billing_workspace()
    drive_billing_cycle("stable-republish")
    buffer = json.loads(BUFFER_JSON.read_text(encoding="utf-8"))
    ref = reference_staging("stable-republish", FIXTURE_ROOT)
    assert buffer["buffer_digest"] == ref["buffer_digest"]
    assert buffer["segments"] == ref["segments"]


def test_proration_reconcile_pass_increments() -> None:
    """publish report must echo pass counter after reconcile-entitlements completes per invoice-publish-contract."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    ref = reference_invoices("clean-monthly", FIXTURE_ROOT)
    assert body["reconcile_pass"] == ref["reconcile_pass"]


def test_proration_publish_blocked_without_reconcile() -> None:
    """publish-invoices must refuse when reconcile_pass is zero per invoice-publish-contract."""
    reset_billing_workspace()
    subprocess.run(
        [CTL_BIN, "load-cycle", "--scenario", "clean-monthly", "--fixture-dir", str(FIXTURE_ROOT)],
        cwd="/app",
        check=True,
    )
    proc = subprocess.run(
        [CTL_BIN, "publish-invoices", "--scenario", "clean-monthly"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_proration_decoy_catalog_isolated_from_invoice() -> None:
    """Decoy plandisplay catalog strings must not appear in subscription invoice JSON per decoy-plandisplay-contract."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    serialized = json.dumps(body)
    assert "plan " not in serialized or "monthly=" not in serialized


def test_proration_duplicate_safe_republish_same_digest() -> None:
    """Repeated pipeline on stable-republish must keep identical ledger_digest."""
    reset_billing_workspace()
    drive_billing_cycle("stable-republish")
    first = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    drive_billing_cycle("stable-republish")
    second = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert first["ledger_digest"] == second["ledger_digest"]


def test_proration_buffer_file_written_on_reconcile() -> None:
    """reconcile-entitlements must write /app/work/entitlement-buffer.json before publish."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    assert BUFFER_JSON.is_file()
    buffer = json.loads(BUFFER_JSON.read_text(encoding="utf-8"))
    assert "segments" in buffer
    assert "buffer_digest" in buffer


def test_proration_customer_id_echoed_in_report() -> None:
    """subscription-invoices.json must echo randomized customer_id from scenario fixture."""
    reset_billing_workspace()
    drive_billing_cycle("clean-monthly")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    ref = reference_invoices("clean-monthly", FIXTURE_ROOT)
    assert body["customer_id"] == ref["customer_id"]


def test_proration_overage_line_when_usage_exceeds_included() -> None:
    """Usage above included_units must produce positive overage_cents on invoice line."""
    reset_billing_workspace()
    drive_billing_cycle("coupon-single")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"][0]["overage_cents"] > 0


def test_proration_multi_segment_base_cents_positive() -> None:
    """Each segment in multi-event cycle must carry positive base_cents allocation."""
    reset_billing_workspace()
    drive_billing_cycle("multi-event")
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert all(line["base_cents"] > 0 for line in body["invoice_lines"])
