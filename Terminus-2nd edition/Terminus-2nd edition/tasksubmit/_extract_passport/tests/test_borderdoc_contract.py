"""Contract probes — ingest-stage manifest snapshot vs scoring vs export-stage seal layers."""

from __future__ import annotations

import json
import sqlite3

from validity_refmath import reference_decisions
from validity_runner import (
    DB_PATH,
    DECISION_JSON,
    FIXTURE_ROOT,
    LEDGER_JSON,
    BORDERDOC_BIN,
    invoke,
    run_eval_only,
    run_pipeline,
    wipe_state,
)


def test_bdoc_staging_decisions_buffer_matches_reference() -> None:
    """SQLite decisions must match reference after score-validity."""
    wipe_state()
    run_eval_only("visa-span-outside")
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute(
            "SELECT holder_id, visa_id, allowed_entry, cumulative_stay_days FROM decisions ORDER BY holder_id, visa_id"
        ).fetchall()
    finally:
        con.close()
    ref = reference_decisions("visa-span-outside", FIXTURE_ROOT)
    got = [
        {
            "holder_id": r[0],
            "visa_id": r[1],
            "allowed_entry": bool(r[2]),
            "cumulative_stay_days": r[3],
        }
        for r in rows
    ]
    for g, e in zip(got, ref["decisions"]):
        assert g["holder_id"] == e["holder_id"]
        assert g["allowed_entry"] == e["allowed_entry"]


def test_bdoc_manifest_only_load_fails_commit() -> None:
    """Manifest-only load without score-validity must block commit-ledger."""
    wipe_state()
    invoke(
        [
            BORDERDOC_BIN,
            "import-manifest",
            "--scenario",
            "clean-entry",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    proc = invoke([BORDERDOC_BIN, "commit-ledger", "--scenario", "clean-entry"])
    assert proc.returncode != 0


def test_bdoc_contract_replay_stable_seal_same_digest() -> None:
    """Repeated commit-ledger with same eval_pass yields identical ledger_digest."""
    wipe_state()
    run_eval_only("clean-entry")
    invoke([BORDERDOC_BIN, "commit-ledger", "--scenario", "clean-entry"])
    first = json.loads(LEDGER_JSON.read_text(encoding="utf-8"))
    invoke([BORDERDOC_BIN, "commit-ledger", "--scenario", "clean-entry"])
    second = json.loads(LEDGER_JSON.read_text(encoding="utf-8"))
    assert first["ledger_digest"] == second["ledger_digest"]
    assert first["ledger_rows"] == second["ledger_rows"]


def test_bdoc_contract_ledger_rows_not_doubled_on_rerun() -> None:
    """Second publish must not duplicate ledger table rows."""
    wipe_state()
    run_pipeline("clean-entry")
    con = sqlite3.connect(DB_PATH)
    try:
        n = con.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
    finally:
        con.close()
    invoke([BORDERDOC_BIN, "commit-ledger", "--scenario", "clean-entry"])
    con = sqlite3.connect(DB_PATH)
    try:
        n2 = con.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
    finally:
        con.close()
    assert n == n2


def test_bdoc_contract_eval_pass_gate_blocks_early_publish() -> None:
    """score-validity must run before commit-ledger succeeds."""
    wipe_state()
    invoke(
        [
            BORDERDOC_BIN,
            "import-manifest",
            "--scenario",
            "federal-precedence",
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    proc = invoke([BORDERDOC_BIN, "commit-ledger", "--scenario", "federal-precedence"])
    assert proc.returncode != 0
    run_eval_only("federal-precedence")
    proc = invoke([BORDERDOC_BIN, "commit-ledger", "--scenario", "federal-precedence"])
    assert proc.returncode == 0


def test_bdoc_contract_decisions_json_matches_sqlite() -> None:
    """validity-decisions.json must mirror decisions table."""
    wipe_state()
    run_eval_only("cumulative-stay")
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    con = sqlite3.connect(DB_PATH)
    try:
        count = con.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    finally:
        con.close()
    assert len(body["decisions"]) == count
