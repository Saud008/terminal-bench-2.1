"""Subprocess harness for shadedrift CLI invocations."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "shadedrift"
CORR_SNAP_DIR = APP / "state" / "shade-correlation"


def wipe() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def invoke(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        args,
        cwd=str(APP),
        env=merged,
        text=True,
        capture_output=True,
        timeout=120,
    )


def pipeline(
    scenario: str,
    run_id: str,
    *,
    scenario_root: Path | None = None,
) -> Path:
    env: dict[str, str] = {}
    if scenario_root is not None:
        env["TB3_SCENARIO_ROOT"] = str(scenario_root)
    for cmd in (
        ["ingest-scenario", "--scenario", scenario, "--run-id", run_id],
        ["correlate", "--run-id", run_id],
    ):
        proc = invoke([str(CLI), *cmd], env=env or None)
        assert proc.returncode == 0, proc.stderr
    out = APP / "output" / f"{run_id}-drift.json"
    proc = invoke(
        [str(CLI), "export-report", "--run-id", run_id, "--output", str(out)],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr
    return out
