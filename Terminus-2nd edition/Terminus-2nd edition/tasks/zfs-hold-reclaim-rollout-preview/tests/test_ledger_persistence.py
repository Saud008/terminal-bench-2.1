"""Ledger persistence and load_seq advancement contracts."""

from __future__ import annotations

from pathlib import Path

from zfshold_cli_support import read_json, reset_state, run_cli


def test_load_seq_advances_and_ledger_persists() -> None:
    """Second load advances load_seq; publish reuses reclaim-ledger without recompile."""
    reset_state()
    run_cli(["load", "--scenario", "basic-hold", "--run-id", "persist-1"])
    inv1 = read_json("/app/state/inventory.json")
    assert inv1["load_seq"] == 1
    run_cli(["load", "--scenario", "basic-hold", "--run-id", "persist-1"])
    inv2 = read_json("/app/state/inventory.json")
    assert inv2["load_seq"] == 2
    meta = read_json("/app/state/run-meta.json")
    assert meta["load_seq"] == 2
    run_cli(["compile", "--run-id", "persist-1"])
    ledger = read_json("/app/state/reclaim-ledger.json")
    assert ledger["load_seq"] == 2
    run_id_before = ledger["run_id"]
    eligible_before = ledger["eligible"]
    run_cli(
        [
            "publish",
            "--run-id",
            "persist-1",
            "--output",
            "/app/output/zfs_reclaim_rollout_atlas.json",
        ]
    )
    atlas = read_json("/app/output/zfs_reclaim_rollout_atlas.json")
    assert atlas["run_id"] == run_id_before
    assert atlas["eligible"] == eligible_before
    assert Path("/app/state/reclaim-ledger.json").is_file()
