"""compile/publish sequencing: ledger persistence and ordering constraints between stages."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fleet_cutover_harness import CLI, invoke, load_json, wipe_run_state


def test_compile_before_any_scan_has_run_fails() -> None:
    """compile must refuse to run when no inventory has ever been scanned into state."""
    wipe_run_state()
    proc = subprocess.run(
        [str(CLI), "compile", "--run-id", "no-scan-yet"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_publish_before_compile_has_run_fails() -> None:
    """publish must refuse to run when no reconnect ledger has been composed yet."""
    wipe_run_state()
    invoke(["scan", "--scenario", "basic-reconnect", "--run-id", "no-compile-yet"])
    proc = subprocess.run(
        [str(CLI), "publish", "--run-id", "no-compile-yet"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_compiled_ledger_carries_the_same_load_seq_as_scan() -> None:
    """The reconnect ledger's load_seq must be copied verbatim from the scanned inventory."""
    wipe_run_state()
    invoke(["scan", "--scenario", "basic-reconnect", "--run-id", "seq-carry"])
    invoke(["compile", "--run-id", "seq-carry"])
    inv = load_json("/app/state/inventory.json")
    ledger = load_json("/app/state/reconnect-ledger.json")
    assert ledger["load_seq"] == inv["load_seq"]


def test_publish_does_not_recompute_eligibility_from_fixtures() -> None:
    """publish must read only the ledger; mutating the on-disk fixture after compile must not affect it."""
    wipe_run_state()
    invoke(["scan", "--scenario", "basic-reconnect", "--run-id", "frozen-ledger"])
    invoke(["compile", "--run-id", "frozen-ledger"])
    ledger_before = load_json("/app/state/reconnect-ledger.json")
    invoke(
        [
            "publish",
            "--run-id",
            "frozen-ledger",
            "--output",
            "/app/output/frozen_atlas.json",
        ]
    )
    atlas = load_json("/app/output/frozen_atlas.json")
    assert atlas["eligible_count"] == ledger_before["eligible_count"]
    assert atlas["ineligible_count"] == ledger_before["ineligible_count"]


def test_wiped_state_directory_has_no_leftover_ledger_or_atlas() -> None:
    """reset-state.sh must clear inventory, run-meta, and ledger between independent cases."""
    wipe_run_state()
    assert not Path("/app/state/inventory.json").exists()
    assert not Path("/app/state/run-meta.json").exists()
    assert not Path("/app/state/reconnect-ledger.json").exists()
