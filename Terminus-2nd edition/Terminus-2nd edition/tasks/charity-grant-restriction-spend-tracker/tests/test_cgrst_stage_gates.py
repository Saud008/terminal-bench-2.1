"""Staging and export split contract tests."""

from __future__ import annotations

import json
import sqlite3

from cgrst_driver import BIN, DB_PATH, FIXTURE_ROOT, PASS_JSON, invoke, wipe_state


def test_grant_contract_staging_tables_after_apply() -> None:
    """apply-amendments staging must materialize balances before export."""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "multi-grant-balance", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke([BIN, "apply-amendments"])
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute(
            "SELECT grant_id, spent_cents, remaining_cents FROM staged_balances ORDER BY grant_id"
        ).fetchall()
    finally:
        con.close()
    assert len(rows) == 2
    assert rows[0][0] == "G-FOOD"


def test_grant_contract_ingest_only_cannot_publish() -> None:
    """ingest-only load-portfolio must block publish-spend-atlas export."""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "staging-gate", "--fixture-dir", str(FIXTURE_ROOT)])
    proc = invoke([BIN, "publish-spend-atlas"])
    assert proc.returncode != 0


def test_grant_contract_apply_then_publish_succeeds() -> None:
    """positive amendment_pass must allow publish-spend-atlas success."""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "staging-gate", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke([BIN, "apply-amendments"])
    proc = invoke([BIN, "publish-spend-atlas"])
    assert proc.returncode == 0


def test_grant_contract_pass_file_tracks_apply_runs() -> None:
    """/app/state/amendment-pass.json must count apply-amendments invocations."""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "staging-gate", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke([BIN, "apply-amendments"])
    invoke([BIN, "apply-amendments"])
    body = json.loads(PASS_JSON.read_text(encoding="utf-8"))
    assert body["amendment_pass"] == 2


def test_grant_contract_publish_rerun_is_stable() -> None:
    """publish-spend-atlas reruns must remain stable within one amendment pass."""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "rerun-idempotent", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke([BIN, "apply-amendments"])
    first = invoke([BIN, "publish-spend-atlas"])
    second = invoke([BIN, "publish-spend-atlas"])
    assert first.returncode == 0
    assert second.returncode == 0
