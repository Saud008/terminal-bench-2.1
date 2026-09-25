"""CLI harness for shift-pl."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
BIN = APP / "bin" / "shift-pl"
STAGING = APP / "state" / "shift-harmonized.json"
DEFAULT = APP / "fixtures" / "scenarios"


def scenario_root() -> Path:
    root = os.environ.get("SHIFT_SCENARIO_ROOT")
    return Path(root) if root else DEFAULT


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def rebuild() -> None:
    run(["bash", str(APP / "scripts" / "rebuild-shift-pl.sh")])


def wipe() -> None:
    run(["bash", str(APP / "scripts" / "reset-state.sh")])


def pipeline(scenario: str, run_id: str, out: Path | None = None) -> Path:
    out = out or APP / "output" / f"{run_id}.json"
    wipe()
    rebuild()
    run([str(BIN), "latch", "--scenario", scenario, "--run-id", run_id])
    run([str(BIN), "curate", "--run-id", run_id])
    run([str(BIN), "publish", "--run-id", run_id, "--output", str(out)])
    return out


def load_staging() -> dict:
    return json.loads(STAGING.read_text(encoding="utf-8"))
