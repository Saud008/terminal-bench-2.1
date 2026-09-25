"""Ledger persistence and load_seq advancement contracts."""

from __future__ import annotations

import subprocess

from mdreshape_harness import CLI, read_json, reset_state, run_cli


def test_mdreshape_run_counter_bumps_and_reshape_ledger_stays() -> None:
    """Second scan advances load_seq; publish reuses reshape-ledger staging snapshot without recompile."""
    reset_state()
    run_cli(["scan", "--scenario", "basic-reshape", "--run-id", "persist-1"])
    inv1 = read_json("/app/state/inventory.json")
    assert inv1["load_seq"] == 1
    run_cli(["scan", "--scenario", "basic-reshape", "--run-id", "persist-1"])
    inv2 = read_json("/app/state/inventory.json")
    assert inv2["load_seq"] == 2
    meta = read_json("/app/state/run-meta.json")
    assert meta["load_seq"] == 2
    run_cli(["compile", "--run-id", "persist-1"])
    ledger = read_json("/app/state/reshape-ledger.json")
    assert ledger["load_seq"] == 2
    run_id_before = ledger["run_id"]
    eligible_before = ledger["eligible"]
    run_cli(
        [
            "publish",
            "--run-id",
            "persist-1",
            "--output",
            "/app/output/mdreshape_eligibility_atlas.json",
        ]
    )
    atlas = read_json("/app/output/mdreshape_eligibility_atlas.json")
    assert atlas["run_id"] == run_id_before
    assert atlas["eligible"] == eligible_before
    # staging snapshot on disk must still be present for replay checks
    assert ledger["eligible_count"] == atlas["eligible_count"]


def test_mdreshape_compile_fails_without_fleet_state() -> None:
    """compile must fail when no inventory has been scanned into state yet."""
    reset_state()
    proc = subprocess.run(
        [str(CLI), "compile", "--run-id", "no-scan"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_mdreshape_publish_fails_without_reshape_ledger() -> None:
    """publish must fail when no ledger has been compiled into state yet."""
    reset_state()
    run_cli(["scan", "--scenario", "basic-reshape", "--run-id", "no-compile"])
    proc = subprocess.run(
        [str(CLI), "publish", "--run-id", "no-compile", "--output", "/app/output/mdreshape_eligibility_atlas.json"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
