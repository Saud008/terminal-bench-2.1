"""Hidden TB3 traps — different failure modes than bundled scenarios."""

from __future__ import annotations

import json
import os
from pathlib import Path

from cycle_harness import INVOICE_JSON, drive_billing_cycle, reset_billing_workspace
from entitlement_calc import reference_invoices

HIDDEN_ROOT = Path("/opt/verifier-fixtures/subledctl")


def test_contract_hidden_coupon_stack_trap() -> None:
    """Exclusive coupon must beat stackable fixed discount on hidden fixture."""
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    reset_billing_workspace()
    drive_billing_cycle("hidden-coupon-stack", HIDDEN_ROOT)
    ref = reference_invoices("hidden-coupon-stack", HIDDEN_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"] == ref["invoice_lines"]
    os.environ.pop("TB3_FIXTURE_DIR", None)


def test_contract_hidden_prorate_same_day_change() -> None:
    """Plan change on cycle start must produce single prorated segment."""
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    reset_billing_workspace()
    drive_billing_cycle("hidden-prorate-edge", HIDDEN_ROOT)
    ref = reference_invoices("hidden-prorate-edge", HIDDEN_ROOT)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoice_lines"] == ref["invoice_lines"]
    os.environ.pop("TB3_FIXTURE_DIR", None)
