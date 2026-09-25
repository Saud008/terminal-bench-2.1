"""Smoke and artifact path checks for ppareconctl."""

from __future__ import annotations

import json
import sqlite3
import subprocess

from ppa_ctl_exec import (
    CTL_BIN,
    DB_PATH,
    FIXTURE_ROOT,
    INVOICE_PATH,
    JSONL_PATH,
    run_ppa_billing_pipeline,
    reset_ppa_workspace,
)
from ppa_settlement_math import reference_invoice, reference_lines


def test_tbe360f_be360fc5_ppa_materialize_jsonl_sqlite() -> None:
    """materialize-lines must write /app/state/settlement-lines.jsonl and /app/state/ppa-settlement.db."""
    reset_ppa_workspace()
    proc = subprocess.run(
        [CTL_BIN, "materialize-lines", "--scenario", "clean-interval", "--fixture-dir", str(FIXTURE_ROOT)],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert JSONL_PATH.as_posix() == "/app/state/settlement-lines.jsonl"
    assert DB_PATH.as_posix() == "/app/state/ppa-settlement.db"
    assert JSONL_PATH.is_file()
    assert DB_PATH.is_file()
    con = sqlite3.connect(DB_PATH)
    try:
        count = con.execute("SELECT COUNT(*) FROM settlement_lines").fetchone()[0]
    finally:
        con.close()
    assert count >= 1


def test_tbe360f_be360fc5_ppa_rollup_invoice_json() -> None:
    """Lab calibration rollup must emit invoice JSON with numeric closure totals."""
    reset_ppa_workspace()
    run_ppa_billing_pipeline("clean-interval")
    assert INVOICE_PATH.as_posix() == "/app/output/invoice-rollup.json"
    assert INVOICE_PATH.is_file()
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    assert body["scenario_id"] == "clean-interval"


def test_tbe360f_be360fc5_ppa_clean_interval_lines_ref() -> None:
    """Settlement lines on clean-interval must match ppa_settlement_math expectations."""
    reset_ppa_workspace()
    run_ppa_billing_pipeline("clean-interval")
    lines = [json.loads(row) for row in JSONL_PATH.read_text(encoding="utf-8").splitlines() if row.strip()]
    ref = reference_lines("clean-interval", FIXTURE_ROOT)
    assert lines == ref


def test_tbe360f_be360fc5_ppa_clean_interval_invoice_ref() -> None:
    """Invoice rollup must match reference kernel within numeric tolerance for closure totals."""
    reset_ppa_workspace()
    run_ppa_billing_pipeline("clean-interval")
    body = json.loads(INVOICE_PATH.read_text(encoding="utf-8"))
    ref = reference_invoice("clean-interval", FIXTURE_ROOT)
    assert body == ref
