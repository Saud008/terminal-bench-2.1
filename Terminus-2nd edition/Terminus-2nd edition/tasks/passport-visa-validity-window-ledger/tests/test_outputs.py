"""Smoke and bundled passport validity scenarios."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess

from validity_refmath import reference_decisions
from validity_runner import (
    BORDERDOC_BIN,
    DB_PATH,
    DECISION_JSON,
    FIXTURE_ROOT,
    PASS_JSON,
    SNAPSHOT_JSON,
    invoke,
    materialize_seed_fixtures,
    run_eval_only,
    run_pipeline,
    wipe_state,
)


def test_pvvwl_smoke_load_creates_sqlite_bundle() -> None:
    """import-manifest must create /app/state/border-validity.db with passport rows."""
    wipe_state()
    proc = subprocess.run(
        [
            BORDERDOC_BIN,
            "import-manifest",
            "--scenario",
            "clean-entry",
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
        passports = con.execute("SELECT COUNT(*) FROM passports").fetchone()[0]
        visas = con.execute("SELECT COUNT(*) FROM visas").fetchone()[0]
    finally:
        con.close()
    assert passports == 1
    assert visas == 1


def test_pvvwl_clean_entry_decisions_match_reference() -> None:
    """clean-entry decisions must match independent reference math."""
    wipe_state()
    run_pipeline("clean-entry")
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    ref = reference_decisions("clean-entry", FIXTURE_ROOT)
    assert body["decisions"] == ref["decisions"]
    assert body["ledger_digest"] == ref["ledger_digest"]


def test_pvvwl_expiry_edge_inclusive_on_expiry_day() -> None:
    """Passport valid on expiry day per passport-window-contract."""
    wipe_state()
    run_pipeline("expiry-edge")
    ref = reference_decisions("expiry-edge", FIXTURE_ROOT)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"] == ref["decisions"]
    assert body["decisions"][0]["allowed_entry"] is True


def test_pvvwl_visa_span_outside_passport_denied() -> None:
    """Visa span outside passport window denies per visa-overlap-contract."""
    wipe_state()
    run_pipeline("visa-span-outside")
    ref = reference_decisions("visa-span-outside", FIXTURE_ROOT)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"] == ref["decisions"]
    assert "visa_overlap" in body["decisions"][0]["deny_reasons"]


def test_pvvwl_cumulative_stay_sums_closed_stamps() -> None:
    """Closed stamps accumulate inclusive stay days."""
    wipe_state()
    run_pipeline("cumulative-stay")
    ref = reference_decisions("cumulative-stay", FIXTURE_ROOT)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"][0]["cumulative_stay_days"] == ref["decisions"][0]["cumulative_stay_days"]
    assert body["decisions"][0]["cumulative_stay_days"] == 26


def test_pvvwl_grace_overstay_denies_after_grace() -> None:
    """Open visit beyond max_stay plus grace denies entry."""
    wipe_state()
    run_pipeline("grace-overstay")
    ref = reference_decisions("grace-overstay", FIXTURE_ROOT)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"] == ref["decisions"]
    assert body["decisions"][0]["allowed_entry"] is False


def test_pvvwl_federal_precedence_beats_port_cap() -> None:
    """Federal max_stay applies over port cap per rule-precedence-contract."""
    wipe_state()
    run_pipeline("federal-precedence")
    ref = reference_decisions("federal-precedence", FIXTURE_ROOT)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"] == ref["decisions"]
    assert body["decisions"][0]["max_stay_allowed"] == 90


def test_pvvwl_revoked_passport_suppresses_visa() -> None:
    """Revoked passport denies linked visa per revoke-suppression-contract."""
    wipe_state()
    run_pipeline("revoked-passport")
    ref = reference_decisions("revoked-passport", FIXTURE_ROOT)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"] == ref["decisions"]
    assert "document_revoked" in body["decisions"][0]["deny_reasons"]


def test_pvvwl_active_hold_blocks_entry() -> None:
    """Active watchlist hold denies per watchlist-hold-contract."""
    wipe_state()
    run_pipeline("active-hold")
    ref = reference_decisions("active-hold", FIXTURE_ROOT)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"] == ref["decisions"]
    assert "watchlist_hold" in body["decisions"][0]["deny_reasons"]


def test_pvvwl_open_stamp_counts_through_reference() -> None:
    """Open stamp tail counts through reference_date inclusive."""
    wipe_state()
    run_pipeline("open-stamp-tail")
    ref = reference_decisions("open-stamp-tail", FIXTURE_ROOT)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"][0]["cumulative_stay_days"] == ref["decisions"][0]["cumulative_stay_days"]


def test_pvvwl_eval_pass_increments() -> None:
    """score-validity must bump /app/state/eval-pass.json."""
    wipe_state()
    run_pipeline("clean-entry")
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["eval_pass"] == 1


def test_pvvwl_eval_pass_json_path() -> None:
    """eval-pass.json lives under /app/state with integer pass counter."""
    wipe_state()
    run_pipeline("clean-entry")
    body = json.loads(PASS_JSON.read_text(encoding="utf-8"))
    assert PASS_JSON.as_posix() == "/app/state/eval-pass.json"
    assert body["eval_pass"] == 1


def test_pvvwl_manifest_snapshot_written_on_load() -> None:
    """import-manifest writes manifest snapshot at /app/state/manifest-snapshot.json."""
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
    snap = json.loads(SNAPSHOT_JSON.read_text(encoding="utf-8"))
    assert snap["scenario_id"] == "clean-entry"
    assert snap["passport_count"] == 1


def test_pvvwl_publish_requires_positive_eval_pass() -> None:
    """commit-ledger rejects when eval_pass is zero."""
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


def test_pvvwl_decisions_sorted_by_holder_then_visa() -> None:
    """Decision rows sorted by holder_id then visa_id."""
    wipe_state()
    run_pipeline("clean-entry")
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    holders = [row["holder_id"] for row in body["decisions"]]
    assert holders == sorted(holders)


def test_pvvwl_decision_output_path() -> None:
    """validity-decisions.json lives under /app/output."""
    wipe_state()
    run_eval_only("clean-entry")
    assert DECISION_JSON.as_posix() == "/app/output/validity-decisions.json"
    assert DECISION_JSON.is_file()


def test_pvvwl_remaining_stay_non_negative() -> None:
    """remaining_stay_days never negative on allowed scenarios."""
    wipe_state()
    run_pipeline("cumulative-stay")
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"][0]["remaining_stay_days"] >= 0


def test_pvvwl_pvw_seed_anti_hardcoding() -> None:
    """Already-remapped seeded fixture IDs must be consumed without CLI remapping."""
    wipe_state()
    seed = os.environ.get("BORDERDOC_SEED", "991122")
    root = materialize_seed_fixtures("clean-entry", seed, FIXTURE_ROOT)
    env = {"BORDERDOC_SEED": seed}
    invoke(
        [BORDERDOC_BIN, "import-manifest", "--scenario", "clean-entry", "--fixture-dir", str(root)],
        env=env,
    )
    invoke([BORDERDOC_BIN, "score-validity", "--scenario", "clean-entry"], env=env)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    ref = reference_decisions("clean-entry", root)
    assert body["decisions"] == ref["decisions"]
