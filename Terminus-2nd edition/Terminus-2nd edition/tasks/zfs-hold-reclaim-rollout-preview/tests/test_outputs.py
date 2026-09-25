"""End-to-end atlas checks for the basic-hold fleet rollout fixture."""

from __future__ import annotations

import subprocess
from pathlib import Path

from zfshold_cli_support import load_compile_publish, reset_state
from zfshold_contract_math import audit_digest, load_scenario, reference_evaluate


def test_cli_installed_for_host_rollout() -> None:
    """Fleet host rollout CLI binary must be installed at /app/bin/zfshold."""
    assert Path("/app/bin/zfshold").is_file()
    proc = subprocess.run(["/app/bin/zfshold"], capture_output=True, text=True)
    assert proc.returncode != 0


def test_basic_hold_fleet_rollout_atlas_matches_reference() -> None:
    """Fleet reclaim rollout atlas for basic-hold must match independent host math."""
    reset_state()
    atlas = load_compile_publish(
        "basic-hold",
        "t-basic",
        output="/app/output/zfs_reclaim_rollout_atlas.json",
    )
    assert Path("/app/state/reclaim-ledger.json").is_file()
    assert Path("/app/state/run-meta.json").is_file()
    assert Path("/app/output/zfs_reclaim_rollout_atlas.json").is_file()
    inv = load_scenario(Path("/app/fixtures/scenarios/basic-hold/inventory.json"))
    ref = reference_evaluate(inv)
    assert atlas["eligible_count"] == ref["eligible_count"]
    assert atlas["blocked_count"] == ref["blocked_count"]
    assert {r["name"] for r in atlas["eligible"]} == {r["name"] for r in ref["eligible"]}
    assert {r["name"]: r["block_reason"] for r in atlas["blocked"]} == {
        r["name"]: r["block_reason"] for r in ref["blocked"]
    }
    assert atlas["audit_digest"] == audit_digest(ref["eligible"])
    assert atlas["focus_snapshots"] == ["tank/app@free"]
    assert "tank/app@keep" in {r["name"] for r in atlas["blocked"]}
    assert "tank/app@free" in {r["name"] for r in atlas["eligible"]}
