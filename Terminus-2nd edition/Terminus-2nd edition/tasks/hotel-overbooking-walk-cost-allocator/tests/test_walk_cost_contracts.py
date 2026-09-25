"""Hotel finance policy tests — maintenance, loyalty, substitution, demand, walk-cost contracts."""

from __future__ import annotations

import subprocess
from pathlib import Path

from hotel_finance_sim import atlas_total_walk_cost, simulate_capacity_snapshot, simulate_displacement_atlas
from overbook_session import (
    ATLAS_JSON,
    CLI_BIN,
    FIXTURE_ROOT,
    SCENARIO_CLEAN,
    SCENARIO_DEMAND,
    SCENARIO_IDEM,
    SCENARIO_LOYALTY,
    SCENARIO_MAINT,
    SCENARIO_OVERBOOK,
    SCENARIO_SUBST,
    SCENARIO_WALK,
    SNAPSHOT_JSON,
    execute_overbook_night,
    invoke,
    read_json,
    reset_overbook_workspace,
)


def reference_hotel_displacement_atlas(fixture_root, scenario):
    return simulate_displacement_atlas(fixture_root, scenario)


def reference_hotel_capacity_snapshot(fixture_root, scenario):
    return simulate_capacity_snapshot(fixture_root, scenario)


def test_hrev_cli_missing_subcommand():
    """CLI without subcommand exits non-zero."""
    proc = subprocess.run([str(CLI_BIN)], capture_output=True, text=True, check=False)
    assert proc.returncode != 0


def test_hrev_capacity_fingerprint_matches_sim():
    """freeze-capacity-snapshot fingerprint matches reference_hotel_capacity_snapshot."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_CLEAN)
    body = read_json(SNAPSHOT_JSON)
    ref = reference_hotel_capacity_snapshot(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert body["capacity_fingerprint"] == ref["capacity_fingerprint"]


def test_hrev_plan_scores_json_rows():
    """solve-overbook-plan writes scored rows to /app/work/overbook-plan-scores.json."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_CLEAN)
    scores = read_json(Path("/app/work/overbook-plan-scores.json"))
    assert scores["scenario"] == SCENARIO_CLEAN
    assert len(scores["scores"]) >= 2


def test_hrev_publish_blocked_without_solve():
    """export-displacement-atlas fails when solve_pass is zero."""
    reset_overbook_workspace()
    proc = subprocess.run(
        [str(CLI_BIN), "export-displacement-atlas", "--scenario", SCENARIO_CLEAN],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_hrev_ingest_only_blocks_export():
    """ingest-database alone cannot export displacement atlas before solve pass."""
    reset_overbook_workspace()
    proc = invoke(
        [str(CLI_BIN), "ingest-database", "--scenario", SCENARIO_CLEAN, "--fixture-dir", str(FIXTURE_ROOT)]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    export_proc = invoke([str(CLI_BIN), "export-displacement-atlas", "--scenario", SCENARIO_CLEAN])
    assert export_proc.returncode != 0


def test_hrev_overbook_single_walk_rows():
    """overbook-single emits displacement walks when inventory is exhausted."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_OVERBOOK)
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(FIXTURE_ROOT, SCENARIO_OVERBOOK)
    assert len(atlas["walks"]) >= 1
    assert atlas["walks"] == ref["walks"]


def test_hrev_maintenance_block_assignments():
    """maintenance-block honors inclusive blackout windows in assignment counts."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_MAINT)
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(FIXTURE_ROOT, SCENARIO_MAINT)
    assert atlas["assignments"] == ref["assignments"]


def test_hrev_loyalty_shield_walk_order():
    """loyalty-shield walk rank follows protection_rank in loyalty-protection-contract.md."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_LOYALTY)
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(FIXTURE_ROOT, SCENARIO_LOYALTY)
    assert atlas["walks"] == ref["walks"]


def test_hrev_substitution_upgrade_rank():
    """substitution-upgrade assigns a strictly higher room rank when booked type is full."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_SUBST)
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(FIXTURE_ROOT, SCENARIO_SUBST)
    assert atlas["assignments"] == ref["assignments"]
    assert len(atlas["assignments"]) == 1


def test_hrev_demand_ranking_walk_victim():
    """demand-ranking selects walk victims using cancellation-weighted demand scores."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_DEMAND)
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(FIXTURE_ROOT, SCENARIO_DEMAND)
    assert atlas["walks"] == ref["walks"]


def test_hrev_walk_cost_minimization():
    """walk-cost-tie minimizes walk_cost_cents per displacement-cost-contract.md."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_WALK)
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(FIXTURE_ROOT, SCENARIO_WALK)
    assert atlas["walks"] == ref["walks"]
    if atlas["walks"]:
        assert atlas["walks"][0]["walk_cost_cents"] == ref["walks"][0]["walk_cost_cents"]


def test_hrev_aggregate_walk_cost_total():
    """Total walk_cost_cents in displacement atlas matches finance simulator aggregate."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_OVERBOOK)
    atlas = read_json(ATLAS_JSON)
    ref = reference_hotel_displacement_atlas(FIXTURE_ROOT, SCENARIO_OVERBOOK)
    assert atlas_total_walk_cost(atlas) == atlas_total_walk_cost(ref)


def test_hrev_stable_rerun_identical_atlas():
    """stable-rerun yields identical displacement-atlas.json across two full runs."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_IDEM)
    first = ATLAS_JSON.read_text(encoding="utf-8")
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_IDEM)
    second = ATLAS_JSON.read_text(encoding="utf-8")
    assert first == second


def test_hrev_snapshot_maintenance_count():
    """capacity-snapshot maintenance_count reflects maintenance_windows row count."""
    reset_overbook_workspace()
    execute_overbook_night(SCENARIO_MAINT)
    body = read_json(SNAPSHOT_JSON)
    assert body["maintenance_count"] >= 1
