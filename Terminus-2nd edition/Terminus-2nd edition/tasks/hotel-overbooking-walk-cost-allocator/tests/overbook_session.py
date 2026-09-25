from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/overbookctl")
FIXTURE_ROOT = Path("/app/fixtures")
HIDDEN_ROOT = Path("/opt/verifier-fixtures/overbookctl")
SNAPSHOT_JSON = Path("/app/state/capacity-snapshot.json")
ATLAS_JSON = Path("/app/output/displacement-atlas.json")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")

SCENARIO_CLEAN = "clean-night"
SCENARIO_OVERBOOK = "overbook-single"
SCENARIO_MAINT = "maintenance-block"
SCENARIO_LOYALTY = "loyalty-shield"
SCENARIO_SUBST = "substitution-upgrade"
SCENARIO_DEMAND = "demand-ranking"
SCENARIO_WALK = "walk-cost-tie"
SCENARIO_IDEM = "stable-rerun"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def atlas_total_walk_cost(atlas: dict) -> int:
    return sum(int(row.get("walk_cost_cents", 0)) for row in atlas.get("walks", []))


def reset_overbook_workspace() -> None:
    proc = invoke(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def execute_overbook_night(scenario: str, fixture_root: Path | None = None, extra_env: dict | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [str(CLI_BIN), "open-database", "--scenario", scenario, "--fixture-dir", str(root)],
        [str(CLI_BIN), "freeze-capacity-snapshot", "--scenario", scenario],
        [str(CLI_BIN), "solve-overbook-plan", "--scenario", scenario],
        [str(CLI_BIN), "publish-displacement-atlas", "--scenario", scenario],
    )
    for step in steps:
        proc = invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


read_json = load_json
