"""hciroll scan/load intake: fleet ingest of inventory snapshots plus export-ready state.

Covers CLI presence, salted_id derivation, and load_seq counters before compile/export.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from fleet_cutover_harness import CLI, invoke, load_json, wipe_run_state


def test_hciroll_cli_resolves_from_bin_dir() -> None:
    """The hciroll fleet CLI dispatcher must resolve under /app/bin without arguments failing."""
    assert CLI.is_file()
    proc = subprocess.run([str(CLI)], capture_output=True, text=True)
    assert proc.returncode != 0


def test_scan_writes_inventory_and_run_meta_snapshot() -> None:
    """A fresh scan must materialize both state files for a newly registered run."""
    wipe_run_state()
    invoke(["scan", "--scenario", "basic-reconnect", "--run-id", "snap-1"])
    assert Path("/app/state/inventory.json").is_file()
    assert Path("/app/state/run-meta.json").is_file()
    meta = load_json("/app/state/run-meta.json")
    assert meta["scenario"] == "basic-reconnect"
    assert meta["run_id"] == "snap-1"


def test_repeat_scan_advances_load_seq_counter() -> None:
    """Scanning the same host twice without a reset must increment load_seq."""
    wipe_run_state()
    invoke(["scan", "--scenario", "basic-reconnect", "--run-id", "counter-1"])
    first = load_json("/app/state/inventory.json")
    assert first["load_seq"] == 1
    invoke(["scan", "--scenario", "basic-reconnect", "--run-id", "counter-1"])
    second = load_json("/app/state/inventory.json")
    assert second["load_seq"] == 2
    meta = load_json("/app/state/run-meta.json")
    assert meta["load_seq"] == 2


def test_salted_device_identifier_is_stable_across_rescans() -> None:
    """salted_id for a device must not change when the same host is rescanned."""
    wipe_run_state()
    invoke(["scan", "--scenario", "basic-reconnect", "--run-id", "stable-1"])
    before = load_json("/app/state/inventory.json")
    before_id = before["adapters"][0]["devices"][0]["salted_id"]
    invoke(["scan", "--scenario", "basic-reconnect", "--run-id", "stable-1"])
    after = load_json("/app/state/inventory.json")
    after_id = after["adapters"][0]["devices"][0]["salted_id"]
    assert before_id == after_id
    assert len(before_id) == 16
    int(before_id, 16)


def test_scan_without_run_id_flag_exits_nonzero() -> None:
    """scan called without --run-id must fail the flag contract."""
    proc = subprocess.run(
        [str(CLI), "scan", "--scenario", "basic-reconnect"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
