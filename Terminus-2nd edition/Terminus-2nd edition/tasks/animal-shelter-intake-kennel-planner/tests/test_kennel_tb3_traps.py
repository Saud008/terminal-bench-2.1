from __future__ import annotations

import json
from pathlib import Path

from shelter_planner_sim import reference_atlas, reference_bind
from kennel_session import HIDDEN_ROOT, ATLAS_JSON, run_pipeline, wipe_state


def test_kennel_tb3_quarantine_boundary_trap():
    """Verify TB3 quarantine-boundary-trap honors inclusive end_date with TB3_INTAKE_DATE override."""
    scenario = "quarantine-boundary-trap"
    wipe_state()
    run_pipeline(scenario, fixture_root=HIDDEN_ROOT, extra_env={"TB3_INTAKE_DATE": "2026-04-05"})
    bind = json.loads(Path(f"/app/state/intake-bind-{scenario}.json").read_text(encoding="utf-8"))
    ref_bind = reference_bind(HIDDEN_ROOT, scenario)
    assert bind["registry_digest"] == ref_bind["registry_digest"]
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_atlas(HIDDEN_ROOT, scenario)
    assert atlas["placements"] == ref["placements"]


def test_kennel_tb3_transfer_penalty_hidden_trap():
    """Verify TB3 transfer-penalty-hidden-trap selects partner species per hidden fixture contract."""
    scenario = "transfer-penalty-hidden-trap"
    wipe_state()
    run_pipeline(scenario, fixture_root=HIDDEN_ROOT)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_atlas(HIDDEN_ROOT, scenario)
    assert atlas["transfers"] == ref["transfers"]
    assert atlas["transfers"][0]["to_species"] == ref["transfers"][0]["to_species"]
