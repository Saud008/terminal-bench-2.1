from __future__ import annotations

import os
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/ttalloc")
FIXTURE_ROOT = Path("/app/fixtures")
HIDDEN_ROOT = Path("/opt/verifier-fixtures/ttalloc")
GRAPH_JSON = Path("/app/state/constraint-graph.json")
ATLAS_JSON = Path("/app/output/timetable-atlas.json")
CONFLICT_JSON = Path("/app/output/conflict-report.json")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")

SCENARIO_CLEAN = "clean-timetable"
SCENARIO_LAB = "lab-room-required"
SCENARIO_SPLIT = "split-section-sync"
SCENARIO_CAP = "capacity-edge"
SCENARIO_TEACHER = "teacher-double-block"
SCENARIO_STABLE = "stable-score-order"
SCENARIO_MULTI = "multi-section-lab"
SCENARIO_IDEM = "steady-rerun-atlas"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    combined_env = os.environ.copy()
    if env:
        combined_env.update(env)
    return subprocess.run(cmd, cwd="/app", capture_output=True, text=True, check=False, env=combined_env)


def wipe_state() -> None:
    proc = invoke(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(scenario: str, fixture_root: Path | None = None, extra_env: dict | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [str(CLI_BIN), "load-roster", "--scenario", scenario, "--fixture-dir", str(root)],
        [str(CLI_BIN), "materialize-graph", "--scenario", scenario],
        [str(CLI_BIN), "allocate-slots", "--scenario", scenario],
        [str(CLI_BIN), "publish-atlas", "--scenario", scenario],
    )
    for step in steps:
        proc = invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout
