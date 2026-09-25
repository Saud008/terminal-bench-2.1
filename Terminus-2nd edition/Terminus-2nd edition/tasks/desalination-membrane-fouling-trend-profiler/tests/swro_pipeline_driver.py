"""Subprocess helpers for SWRO fouling profiler integration tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
ROTRACE = APP / "bin" / "rotrace"
FIXTURES = APP / "fixtures" / "ro-trains"
RESET = APP / "scripts" / "reset-workspace.sh"
HIDDEN = Path("/opt/verifier-fixtures/rotrace/ro-trains")
LOCAL_HIDDEN = Path("/tests/hidden/ro-trains")


def invoke_rotrace_cli(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def reset_workspace() -> None:
    proc = invoke_rotrace_cli(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def scenario_path(name: str, env: dict | None = None) -> Path:
    if env and env.get("TB3_FIXTURE_ROOT"):
        return Path(env["TB3_FIXTURE_ROOT"]) / name
    return FIXTURES / name


def run_swro_fouling_pipeline(
    run_id: str,
    scenario: str,
    *,
    env: dict | None = None,
    cal_table: str = "",
) -> Path:
    root = scenario_path(scenario, env)
    meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
    base = [str(ROTRACE)]
    load = base + [
        "load-readings",
        "--run-id",
        run_id,
        "--stream",
        str(root / "readings.csv"),
    ]
    if cal_table:
        load += ["--cal-table", cal_table]
    assert invoke_rotrace_cli(load, env).returncode == 0
    assert (
        invoke_rotrace_cli(
            base
            + [
                "bind-cleaning",
                "--run-id",
                run_id,
                "--events",
                str(root / "cleaning.csv"),
                "--membrane",
                str(root / "membrane_batches.json"),
                "--train-id",
                meta["train_id"],
            ],
            env,
        ).returncode
        == 0
    )
    assert invoke_rotrace_cli(base + ["normalize-ndp", "--run-id", run_id], env).returncode == 0
    assert invoke_rotrace_cli(base + ["score-trends", "--run-id", run_id], env).returncode == 0
    out = APP / "output" / f"{run_id}-fouling-trend-chronicle.json"
    assert invoke_rotrace_cli(base + ["publish-chronicle", "--run-id", run_id, "--output", str(out)], env).returncode == 0
    return out
