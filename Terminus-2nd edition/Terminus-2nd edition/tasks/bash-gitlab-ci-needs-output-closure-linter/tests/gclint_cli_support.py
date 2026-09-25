"""CLI helpers for gclint tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "gclint"
RESET = APP / "scripts" / "reset-state.sh"
STAGING = APP / "state" / "gclint-staging.json"
PIPE_DIR = APP / "fixtures" / "pipelines"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def wipe() -> None:
    os.environ.pop("TB3_PIPELINE_DIR", None)
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(name: str, run_id: str, *, pipeline_dir: Path | None = None) -> Path:
    env = {}
    if pipeline_dir is not None:
        env["TB3_PIPELINE_DIR"] = str(pipeline_dir)
    for step in (
        [str(CLI), "ingest", "--pipeline", name, "--run-id", run_id],
        [str(CLI), "analyze", "--run-id", run_id],
    ):
        proc = invoke(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / f"{run_id}-lint.json"
    proc = invoke([str(CLI), "export", "--run-id", run_id, "--output", str(out)], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
