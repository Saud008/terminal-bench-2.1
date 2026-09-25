from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/intakectl")
FIXTURE_ROOT = Path("/app/fixtures")
HIDDEN_ROOT = Path("/opt/verifier-fixtures/intakectl")
BIND_GLOB = Path("/app/state")
ATLAS_JSON = Path("/app/output/placement-atlas.json")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")

SCENARIO_CLEAN = "clean-intake"
SCENARIO_OVERFLOW = "overflow-single"
SCENARIO_QUAR = "quarantine-block"
SCENARIO_HOLD = "hold-precedence"
SCENARIO_UPGRADE = "species-upgrade"
SCENARIO_PRIORITY = "priority-ranking"
SCENARIO_TRANSFER = "transfer-penalty-tie"
SCENARIO_STABLE = "stable-rerun"


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


def wipe_state() -> None:
    proc = invoke(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(
    scenario: str,
    run_id: str | None = None,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
    output_path: Path | None = None,
) -> None:
    rid = run_id or scenario
    root = fixture_root or FIXTURE_ROOT
    out = output_path or ATLAS_JSON
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [
            str(CLI_BIN), "bind", "--registry", "sqlite", "--arrivals", "jsonl",
            "--run-id", rid, "--scenario", scenario, "--fixture-dir", str(root),
        ],
        [str(CLI_BIN), "weave", "--run-id", rid],
        [str(CLI_BIN), "seal", "--run-id", rid, "--output", str(out)],
    )
    for step in steps:
        proc = invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def bind_state_path(run_id: str) -> Path:
    return BIND_GLOB / ("intake-bind-" + run_id + ".json")


def weave_pass_state_path(run_id: str) -> Path:
    return BIND_GLOB / ("weave-pass-" + run_id + ".json")

