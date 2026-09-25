"""CLI harness for k7cal."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
BIN = APP / "bin" / "k7cal"
STAGING = APP / "state" / "evac-lane-ledger.json"
DEFAULT = APP / "fixtures" / "scenarios"


def scenario_root() -> Path:
    root = os.environ.get("EVAC_SCENARIO_ROOT")
    return Path(root) if root else DEFAULT


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    run_env = os.environ.copy()
    run_env.pop("TB3_FIXTURE_DIR", None)
    if env:
        run_env.update(env)
    return subprocess.run(cmd, check=True, capture_output=True, text=True, env=run_env)


def rebuild() -> None:
    run(["bash", str(APP / "scripts" / "rebuild-k7cal.sh")])


def wipe() -> None:
    run(["bash", str(APP / "scripts" / "reset-state.sh")])


def pipeline(scenario: str, run_id: str, out: Path | None = None, *, env: dict[str, str] | None = None) -> Path:
    out = out or APP / "output" / f"{run_id}.json"
    wipe()
    rebuild()
    run_env = os.environ.copy()
    run_env.pop("TB3_FIXTURE_DIR", None)
    if env:
        run_env.update(env)
    subprocess.run([str(BIN), "bind", "--scenario", scenario, "--run-id", run_id], check=True, env=run_env)
    subprocess.run([str(BIN), "weave", "--run-id", run_id], check=True, env=run_env)
    subprocess.run([str(BIN), "seal", "--run-id", run_id, "--output", str(out)], check=True, env=run_env)
    return out


def load_weave_ledger() -> dict:
    return json.loads(STAGING.read_text(encoding="utf-8"))
