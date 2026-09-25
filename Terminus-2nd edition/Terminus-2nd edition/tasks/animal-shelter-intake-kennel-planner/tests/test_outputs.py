"""Pytest entry for intakectl fleet rollout verifier — category-native system-administration contract tests."""

from __future__ import annotations

import json

from kennel_session import (
    ATLAS_JSON,
    SCENARIO_CLEAN,
    bind_state_path,
    run_pipeline,
    weave_pass_state_path,
    wipe_state,
)
from shelter_planner_sim import reference_atlas, reference_bind
from kennel_session import FIXTURE_ROOT

# Verifier contract path literals (instruction + docs alignment)
PLACEMENT_ATLAS_PATH = "/app/output/placement-atlas.json"
BIND_STATE_EXAMPLE = "/app/state/intake-bind-clean-intake.json"
REGISTRY_STATE_EXAMPLE = "/app/state/registry-clean-intake.sqlite"
WEAVE_PASS_EXAMPLE = "/app/state/weave-pass-clean-intake.json"


def test_t33bc37_fleet_rollout_placement_atlas_animalma():
    """Fleet rollout review reads /app/output/placement-atlas.json after weave pass."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert atlas.get("engine") == "intakectl"
    assert isinstance(atlas.get("placements"), list)


def test_t33bc37_fleet_topology_registry_animalbi_animaldi():
    """Fleet topology bind attests registry.sqlite digest before kennel weave rollout."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    bind = json.loads(bind_state_path(SCENARIO_CLEAN).read_text(encoding="utf-8"))
    ref = reference_bind(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert bind["registry_digest"] == ref["registry_digest"]


def test_t33bc37_fleet_config_weave_pass_gate():
    """Daemon-style weave_pass gate blocks seal until operational weave completes."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    body = json.loads(weave_pass_state_path(SCENARIO_CLEAN).read_text(encoding="utf-8"))
    assert body.get("weave_pass", 0) >= 1


def test_t33bc37_host_intake_atlas_matches_reference():
    """Host-level intake atlas matches independent reference math for clean-intake scenario."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_atlas(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert atlas["placements"] == ref["placements"]


def test_t33bc37_fleet_registry_sqlite_materialized_on_animalbi():
    """Bind copies registry.sqlite to /app/state/registry-clean-intake.sqlite per bind-registry-lock contract."""
    wipe_state()
    from kennel_session import invoke, CLI_BIN, FIXTURE_ROOT

    proc = invoke(
        [
            str(CLI_BIN),
            "bind",
            "--registry",
            "sqlite",
            "--arrivals",
            "jsonl",
            "--run-id",
            SCENARIO_CLEAN,
            "--scenario",
            SCENARIO_CLEAN,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    from pathlib import Path

    reg = Path("/app/state") / ("registry-" + SCENARIO_CLEAN + ".sqlite")
    assert reg.is_file()
    assert reg.stat().st_size > 0


def test_t33bc37_weave_jsonl_audit_kinds():
    """Weave emits JSONL audit lines with placement or transfer kind per weave-ledger contract."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    from pathlib import Path

    lines = Path("/app/work/quarantine-weave-clean-intake.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
    assert json.loads(lines[0])["kind"] in {"placement", "transfer"}


def test_t33bc37_seal_blocked_without_weave_pass():
    """Seal refuses placement-atlas publish when weave_pass has not run."""
    wipe_state()
    import subprocess
    from kennel_session import CLI_BIN

    proc = subprocess.run(
        [str(CLI_BIN), "seal", "--run-id", SCENARIO_CLEAN, "--output", str(ATLAS_JSON)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
