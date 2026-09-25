"""Hold governor CLI execution helpers for libhold pipeline stages."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/holdfairctl")
FIXTURE_ROOT = Path("/app/fixtures")
HIDDEN_ROOT = Path("/opt/verifier-fixtures/holdfairctl")
ROLLUP_JSON = Path("/app/state/hold-queue-rollup.json")
ATLAS_JSON = Path("/app/output/hold-assignment-atlas.json")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")

SCENARIO_CLEAN = "clean-queue"
SCENARIO_BRANCH = "branch-routing"
SCENARIO_SUSPEND = "suspension-block"
SCENARIO_TIER = "priority-tiers"
SCENARIO_STABLE = "stable-atlas"
SCENARIO_MULTI = "multi-hold"
SCENARIO_INTER = "interbranch-transfer"


def exec_cmd(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
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


def reset_hold_state() -> None:
    proc = exec_cmd(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_hold_pipeline(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [str(CLI_BIN), "mount-library-db", "--scenario", scenario, "--fixture-dir", str(root)],
        [str(CLI_BIN), "compose-rollup", "--scenario", scenario],
        [str(CLI_BIN), "rank-fair-holds", "--scenario", scenario],
        [str(CLI_BIN), "write-assignment-atlas", "--scenario", scenario],
    )
    for step in steps:
        proc = exec_cmd(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
