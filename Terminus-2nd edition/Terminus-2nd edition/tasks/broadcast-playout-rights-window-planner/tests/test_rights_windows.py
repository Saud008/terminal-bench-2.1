"""Rights window and runway snapshot contract probes."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from bcast_synd_refmath import (
    load_bundle,
    reference_plan,
    reference_runway_edges,
    runway_digest,
)
from bcast_synd_cli import (
    ACTIVE_GRID,
    CLI_BIN,
    FIXTURE_ROOT,
    PLAN_JSON,
    SCENARIO_CLEAN,
    SCENARIO_RIGHTS,
    SCENARIO_STABLE,
    STAGING_JSON,
    run_pipeline,
    wipe_state,
)


def test_import_grid_materializes_active_grid_json():
    """import-grid must write /app/state/active-grid.json and /app/state/scenario-active.json."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    assert Path("/app/state/active-grid.json").is_file()
    assert Path("/app/state/scenario-active.json").is_file()
    body = json.loads(ACTIVE_GRID.read_text(encoding="utf-8"))
    assert body.get("scenario") == SCENARIO_CLEAN
    assert "programs" in body


def test_runway_digest_tracks_bundle_seed():
    """snapshot-runway must write /app/state/runway-snapshot.json with refmath digest."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    assert Path("/app/state/runway-snapshot.json").is_file()
    runway = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    bundle = load_bundle(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert runway["runway_digest"] == runway_digest(bundle)


def test_overlap_scenario_picks_narrowest_rights_window():
    """Rights overlap scenario must pick the narrowest qualifying contract window."""
    wipe_state()
    run_pipeline(SCENARIO_RIGHTS)
    syndicated = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    golden = reference_plan(FIXTURE_ROOT, SCENARIO_RIGHTS)
    assert syndicated["entries"] == golden["entries"]


def test_runway_snapshot_lists_rights_contract_edges():
    """Runway snapshot must include rights_contract edges per runway contract."""
    wipe_state()
    run_pipeline(SCENARIO_RIGHTS)
    runway = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    bundle = load_bundle(FIXTURE_ROOT, SCENARIO_RIGHTS)
    expected_kinds = {edge["kind"] for edge in reference_runway_edges(bundle)}
    assert "rights_contract" in expected_kinds
    assert "rights_contract" in {e["kind"] for e in runway.get("edges", [])}


def test_syndicate_blocked_when_compile_epoch_zero():
    """syndicate-plan must fail when compile-epoch plan_pass is zero."""
    wipe_state()
    blocked = subprocess.run(
        [CLI_BIN, "syndicate-plan", "--scenario", SCENARIO_CLEAN],
        capture_output=True,
        text=True,
        check=False,
    )
    assert blocked.returncode != 0


def test_stable_syndication_row_order_is_deterministic():
    """Stable syndicate order scenario must match refmath tie-break airtime rank."""
    wipe_state()
    run_pipeline(SCENARIO_STABLE)
    body = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    assert body["entries"] == reference_plan(FIXTURE_ROOT, SCENARIO_STABLE)["entries"]


def test_clean_syndication_plan_matches_independent_refmath():
    """Clean playout must syndicate /app/output/syndication-plan.json matching independent refmath."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    assert Path("/app/output/syndication-plan.json").is_file()
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    ref = reference_plan(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert plan["runway_digest"] == ref["runway_digest"]
    assert plan["engine"] == "gridplan"
    assert plan["entries"] == ref["entries"]
