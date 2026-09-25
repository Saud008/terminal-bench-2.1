"""Warehouse slot replen atlas contract probes — latch-yard ingest through emit-atlas export."""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from whslot_refmath import (
    expected_atlas_body,
    expected_sku_rank_board,
    expected_wave_assignments,
)
from whslot_driver import ATLAS_JSON, DB_PATH, FIXTURE_ROOT, WHSLOT_BIN, invoke, run_pipeline

SCENARIO_MATRIX = [
    "capacity-headroom",
    "pallet-break-edge",
    "shift-window-fit",
    "shift-end-inclusive",
    "multi-slot-wave",
]

LATCHED_YARD = Path("/app/state/latched-yard.json")
WAVE_LATCH_PASS = Path("/app/state/wave-latch-pass.json")


def _read_atlas() -> dict:
    return json.loads(ATLAS_JSON.read_text(encoding="utf-8"))


def test_t1f1da2_latch_yard_seeds_slot_ledger(fresh_wsr_yard) -> None:
    """latch-yard must seed /app/state/slot-ledger.db with meta rows."""
    proc = invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    with sqlite3.connect(DB_PATH) as con:
        assert con.execute("SELECT COUNT(*) FROM meta").fetchone()[0] >= 1


def test_t1f1da2_latch_yard_creates_slot_ledger_db_file(fresh_wsr_yard) -> None:
    """latch-yard must create the /app/state/slot-ledger.db sqlite ledger file on disk."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    assert DB_PATH.is_file()


def test_t1f1da2_latch_yard_writes_latched_yard_json(fresh_wsr_yard) -> None:
    """latch-yard must copy bundle bytes into the /app/state/latched-yard.json staging file."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    assert LATCHED_YARD.is_file()
    body = json.loads(LATCHED_YARD.read_text(encoding="utf-8"))
    assert "wave_id" in body and body.get("skus")


def test_t1f1da2_subprocess_latch_yard_only(fresh_wsr_yard) -> None:
    """Verifier invokes whslot latch-yard through subprocess without pytest helpers."""
    proc = subprocess.run(
        [WHSLOT_BIN, "latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0


def test_t1f1da2_emit_atlas_blocked_before_crew_bind(fresh_wsr_yard) -> None:
    """emit-atlas must fail when wave_latch_pass is still zero after draft-wave only."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke(["score-skus"])
    invoke(["draft-wave"])
    assert invoke(["emit-atlas"]).returncode != 0


def test_t1f1da2_wave_latch_pass_json_path_updated(fresh_wsr_yard) -> None:
    """crew-bind must write /app/state/wave-latch-pass.json with wave_latch_pass counter."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke(["score-skus"])
    invoke(["draft-wave"])
    invoke(["crew-bind"])
    assert Path("/app/state/wave-latch-pass.json").is_file()
    gate = json.loads(Path("/app/state/wave-latch-pass.json").read_text(encoding="utf-8"))
    assert gate["wave_latch_pass"] > 0


def test_t1f1da2_slot_ledger_db_path_materialized(fresh_wsr_yard) -> None:
    """latch-yard must materialize /app/state/slot-ledger.db before score-skus runs."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    assert Path("/app/state/slot-ledger.db").is_file()


def test_t1f1da2_crew_bind_writes_wave_latch_pass_json(fresh_wsr_yard) -> None:
    """crew-bind must increment wave_latch_pass in the /app/state/wave-latch-pass.json gate file."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke(["score-skus"])
    invoke(["draft-wave"])
    invoke(["crew-bind"])
    gate = json.loads(WAVE_LATCH_PASS.read_text(encoding="utf-8"))
    assert gate["wave_latch_pass"] > 0


def test_t1f1da2_clean_replen_atlas_matches_reference(fresh_wsr_yard) -> None:
    """Full pipeline must publish /app/output/slot-replen-atlas.json matching reference math."""
    run_pipeline("clean-replen")
    body = _read_atlas()
    ref = expected_atlas_body(FIXTURE_ROOT, "clean-replen")
    assert body["assignments"] == ref["assignments"]
    assert body["atlas_fingerprint"] == ref["atlas_fingerprint"]


@pytest.mark.parametrize("scenario", SCENARIO_MATRIX)
def test_t1f1da2_wave_assignments_match_reference(fresh_wsr_yard, scenario: str) -> None:
    """Parameterized scenarios must match independent wave assignment reference rows."""
    run_pipeline(scenario)
    assert _read_atlas()["assignments"] == expected_wave_assignments(FIXTURE_ROOT, scenario)


def test_t1f1da2_idempotent_pipeline_keeps_wave_task_count(fresh_wsr_yard) -> None:
    """Two consecutive pipeline runs must not duplicate wave_tasks rows for the same task_key."""
    run_pipeline("idempotent-rerun")
    with sqlite3.connect(DB_PATH) as con:
        first = con.execute("SELECT COUNT(*) FROM wave_tasks").fetchone()[0]
    run_pipeline("idempotent-rerun")
    with sqlite3.connect(DB_PATH) as con:
        second = con.execute("SELECT COUNT(*) FROM wave_tasks").fetchone()[0]
    assert first == second
    assert _read_atlas()["atlas_fingerprint"] == expected_atlas_body(FIXTURE_ROOT, "idempotent-rerun")["atlas_fingerprint"]


def test_t1f1da2_sku_score_board_matches_reference_ranks(fresh_wsr_yard) -> None:
    """score-skus must write /app/work/sku-score-board.json ranks matching zone-biased reference."""
    invoke(["latch-yard", "--scenario", "velocity-order", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke(["score-skus"])
    board = json.loads(Path("/app/work/sku-score-board.json").read_text(encoding="utf-8"))["ranks"]
    assert board == expected_sku_rank_board(FIXTURE_ROOT, "velocity-order")


def test_t1f1da2_atlas_fingerprint_stable_on_clean_replen(fresh_wsr_yard) -> None:
    """emit-atlas must emit stable atlas_fingerprint for clean-replen bundled scenario."""
    run_pipeline("clean-replen")
    assert _read_atlas()["atlas_fingerprint"] == expected_atlas_body(FIXTURE_ROOT, "clean-replen")["atlas_fingerprint"]
