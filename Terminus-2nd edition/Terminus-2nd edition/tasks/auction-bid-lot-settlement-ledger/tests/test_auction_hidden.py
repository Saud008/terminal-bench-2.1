"""Hidden traps — TB3 fixture dir."""

from __future__ import annotations

import json
import os
from pathlib import Path

from auct_runner import INVOICE_JSON, run_pipeline, wipe_state
from auction_refmath import reference_invoices


def test_abl_hidden_tie_trap_needs_adjudicate_fix() -> None:
    """Hidden tie scenario requires full tie-break adjudication fix."""
    wipe_state()
    root = Path("/opt/verifier-fixtures/auctctl")
    if os.environ.get("TB3_FIXTURE_DIR"):
        root = Path(os.environ["TB3_FIXTURE_DIR"])
    run_pipeline("hidden-tie-trap", fixture_root=root)
    ref = reference_invoices("hidden-tie-trap", root)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]


def test_abl_hidden_adjust_sign_preserves_credit() -> None:
    """Hidden fixture preserves negative adjustment sign."""
    wipe_state()
    root = Path("/opt/verifier-fixtures/auctctl")
    run_pipeline("hidden-adjust-sign", fixture_root=root)
    ref = reference_invoices("hidden-adjust-sign", root)
    body = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert body["invoices"] == ref["invoices"]
    assert body["invoices"][0]["adjustment_cents"] == -1200
