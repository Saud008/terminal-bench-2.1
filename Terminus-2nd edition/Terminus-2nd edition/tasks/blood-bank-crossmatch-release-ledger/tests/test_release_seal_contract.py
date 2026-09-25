"""Contract probes — matrix buffer vs publish layers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from crossmatch_spec import reference_crossmatch
from hemo_session import PATHS, HemotherapySession


def test_release_seal_contract_matrix_snapshot_schema() -> None:
    session = HemotherapySession()
    session.clear_workspace()
    session.import_panels("rh-negative-guard")
    session.score_compatibility("rh-negative-guard")
    con = sqlite3.connect(PATHS.release_db)
    try:
        rows = con.execute(
            "SELECT patient_id, unit_id, compatible FROM crossmatch_rows ORDER BY patient_id, unit_id"
        ).fetchall()
    finally:
        con.close()
    ref = reference_crossmatch("rh-negative-guard", PATHS.fixture_root)
    snapshot = [{"patient_id": r[0], "unit_id": r[1], "compatible": bool(r[2])} for r in rows]
    expected = [{"patient_id": r["patient_id"], "unit_id": r["unit_id"], "compatible": r["compatible"]} for r in ref]
    assert snapshot == expected


def test_release_seal_contract_ingest_only_blocks_publish() -> None:
    session = HemotherapySession()
    session.clear_workspace()
    session.import_panels("abo-clean-release")
    proc = session.shell([str(PATHS.binary), "seal-releases", "--scenario", "abo-clean-release"])
    assert proc.returncode != 0
    assert not PATHS.ledger_json.exists()


def test_release_seal_contract_antibodies_persisted_in_db() -> None:
    session = HemotherapySession()
    session.clear_workspace()
    session.import_panels("dual-antibody-panel")
    con = sqlite3.connect(PATHS.release_db)
    try:
        abs_rows = con.execute(
            "SELECT antibody FROM patient_antibodies WHERE patient_id='P-DUAL' ORDER BY antibody"
        ).fetchall()
    finally:
        con.close()
    assert [r[0] for r in abs_rows] == ["anti-C", "anti-K"]


def test_release_seal_contract_repeat_seal_row_count() -> None:
    session = HemotherapySession()
    session.clear_workspace()
    session.import_panels("publish-repeat-seal")
    session.score_compatibility("publish-repeat-seal")
    session.seal_releases("publish-repeat-seal")
    session.seal_releases("publish-repeat-seal")
    con = sqlite3.connect(PATHS.release_db)
    try:
        n = con.execute("SELECT COUNT(*) FROM ledger WHERE pass_num=1").fetchone()[0]
    finally:
        con.close()
    assert n == 1


def test_release_seal_contract_matrix_order_follows_collected_at() -> None:
    session = HemotherapySession()
    session.clear_workspace()
    session.import_panels("multi-unit-collect-order")
    session.score_compatibility("multi-unit-collect-order")
    lines = Path("/app/work/compatibility-matrix/multi-unit-collect-order.jsonl").read_text(encoding="utf-8").strip().splitlines()
    unit_ids = [json.loads(line)["unit_id"] for line in lines]
    assert unit_ids == ["U-AB-early", "U-AB-late"]
