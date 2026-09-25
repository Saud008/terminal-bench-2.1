"""Hidden TB3 traps for curtailment boundary and exact market interval lookup."""

from __future__ import annotations

import json

from ppa_ctl_exec import INVOICE_PATH, JSONL_PATH, OVERLAY_FIXTURES, exec_ppareconctl, reset_ppa_workspace
from ppa_settlement_math import reference_invoice, reference_lines


def test_overlay_curtail_end_boundary_not_skipped() -> None:
    """TB3 curtail-end-boundary-trap: aligned interval equal to end_utc must not curtail."""
    reset_ppa_workspace()
    env = {"TB3_FIXTURE_DIR": str(OVERLAY_FIXTURES)}
    for step in (
        ["materialize-lines", "--scenario", "curtail-end-boundary-trap", "--fixture-dir", str(OVERLAY_FIXTURES)],
        ["rollup-billing-invoice", "--scenario", "curtail-end-boundary-trap", "--fixture-dir", str(OVERLAY_FIXTURES)],
    ):
        proc = exec_ppareconctl(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    lines = [json.loads(row) for row in JSONL_PATH.read_text(encoding="utf-8").splitlines() if row.strip()]
    ref = reference_lines("curtail-end-boundary-trap", OVERLAY_FIXTURES)
    assert lines == ref
    assert ref[0]["skipped_curtail"] is False
    assert ref[0]["amount_cents"] > 0


def test_overlay_market_exact_interval_price_used() -> None:
    """TB3 market-exact-interval-trap requires exact interval_start_utc market match."""
    reset_ppa_workspace()
    env = {"TB3_FIXTURE_DIR": str(OVERLAY_FIXTURES)}
    for step in (
        ["materialize-lines", "--scenario", "market-exact-interval-trap", "--fixture-dir", str(OVERLAY_FIXTURES)],
        ["rollup-billing-invoice", "--scenario", "market-exact-interval-trap", "--fixture-dir", str(OVERLAY_FIXTURES)],
    ):
        proc = exec_ppareconctl(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    ref = reference_invoice("market-exact-interval-trap", OVERLAY_FIXTURES)
    assert body["total_amount_cents"] == ref["total_amount_cents"]
    assert body["lines_digest"] == ref["lines_digest"]
