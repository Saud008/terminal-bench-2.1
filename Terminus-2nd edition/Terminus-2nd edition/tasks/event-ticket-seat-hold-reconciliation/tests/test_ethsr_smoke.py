"""ETHSR smoke: ingest load-venue, export publish-status, snapshot fingerprint, repeat-run ledger."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ethsr_driver import (
    CLI_BIN,
    CONFLICT_JSON,
    FIXTURE_ROOT,
    SCENARIO_CLEAN,
    SCENARIO_IDEM,
    SQLITE_OUT,
    STAGING_JSON,
    drive_ethsr_pipeline,
    fetch_sqlite_seat_rows,
    invoke,
    wipe_state,
)
from venue_hold_simulator import reference_reconcile, reference_snapshot


def test_ethsr_B01_binary_on_path():
    """CLI surface: venuetixctl binary is installed at /app/bin/venuetixctl."""
    assert Path(CLI_BIN).is_file()


def test_ethsr_B02_missing_subcommand_nonzero():
    """CLI surface: invoking venuetixctl without a subcommand exits non-zero."""
    import subprocess

    proc = subprocess.run([CLI_BIN], capture_output=True, text=True, check=False)
    assert proc.returncode != 0


def test_ethsr_B03_snapshot_fingerprint_matches_simulator():
    """Seat-hold-snapshot-contract: snapshot-holds writes digest to seat-hold-snapshot.json."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_CLEAN)
    assert STAGING_JSON.is_file()
    body = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    ref = reference_snapshot(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert body["hold_snapshot_digest"] == ref["hold_snapshot_digest"]
    assert body["engine"] == "venuetixctl"


def test_ethsr_B04_sqlite_rows_match_simulator():
    """Venue-ledger-contract: publish-status rows in venue-seat-ledger.sqlite match reference math."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_CLEAN)
    assert SQLITE_OUT.is_file()
    ref = reference_reconcile(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert fetch_sqlite_seat_rows() == ref["assignments"]


def test_ethsr_B05_conflict_ledger_matches_simulator():
    """Venue-ledger-contract: hold-conflict-atlas.json matches independent conflict reference."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_CLEAN)
    assert CONFLICT_JSON.is_file()
    report = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    ref = reference_reconcile(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert report["run_stamp"] == ref["run_stamp"]
    assert report["conflicts"] == ref["conflicts"]


def test_ethsr_B06_map_pass_count_advances_second_pipeline():
    """Repeat-run contract: reconcile-map increments map_pass_count in map-pass-count.json."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_CLEAN)
    pass_path = Path("/app/state/map-pass-count.json")
    assert pass_path.is_file()
    first = json.loads(pass_path.read_text(encoding="utf-8"))
    drive_ethsr_pipeline(SCENARIO_CLEAN)
    second = json.loads(pass_path.read_text(encoding="utf-8"))
    assert second["map_pass_count"] == first["map_pass_count"] + 1


def test_ethsr_B07_publish_rejected_before_reconcile():
    """Venue-ledger-contract: publish-status fails when map_pass_count is zero."""
    wipe_state()
    import subprocess

    proc = subprocess.run(
        [CLI_BIN, "publish-status", "--scenario", SCENARIO_CLEAN],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_ethsr_B08_repeat_run_sqlite_rows_on_repeat():
    """Repeat-run contract: second pipeline run leaves venue-seat-ledger.sqlite rows stable."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_IDEM)
    first = fetch_sqlite_seat_rows()
    drive_ethsr_pipeline(SCENARIO_IDEM)
    second = fetch_sqlite_seat_rows()
    assert first == second
    conn = sqlite3.connect(SQLITE_OUT)
    meta = conn.execute("SELECT scenario, map_pass_count FROM reconcile_meta").fetchone()
    conn.close()
    assert meta is not None


def test_ethsr_B09_load_venue_writes_state_paths():
    """CLI surface: load-venue creates event-venue.sqlite and event-manifest.json under /app/state."""
    wipe_state()
    proc = invoke([str(CLI_BIN), "load-venue", "--scenario", SCENARIO_CLEAN])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert Path("/app/state/event-venue.sqlite").is_file()
    assert Path("/app/state/event-manifest.json").is_file()


def test_ethsr_B10_instruction_output_paths_materialized():
    """Instruction table paths exist after full pipeline: seat-hold-snapshot, map-pass-count, ledger, atlas."""
    wipe_state()
    drive_ethsr_pipeline(SCENARIO_CLEAN)
    assert Path("/app/state/seat-hold-snapshot.json").is_file()
    assert Path("/app/state/map-pass-count.json").is_file()
    assert Path("/app/output/venue-seat-ledger.sqlite").is_file()
    assert Path("/app/output/hold-conflict-atlas.json").is_file()
