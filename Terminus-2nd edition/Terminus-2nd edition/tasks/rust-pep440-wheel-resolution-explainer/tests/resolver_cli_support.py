"""CLI harness for the wheel resolver (load, analyze, emit)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
BIN = APP / "bin" / "whres"
REBUILD = APP / "scripts" / "rebuild-whres.sh"
SNAPSHOT = APP / "state" / "whres-snapshot.json"  # /app/state/whres-snapshot.json
DEFAULT_SCENARIOS = APP / "fixtures" / "scenarios"


def scenario_root() -> Path:
    root = os.environ.get("WHRES_SCENARIO_ROOT")
    return Path(root) if root else DEFAULT_SCENARIOS


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def rebuild() -> None:
    run(["bash", str(REBUILD)])


def wipe() -> None:
    run(["bash", str(APP / "scripts" / "reset-state.sh")])


def invoke(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([str(BIN), *args], check=False, capture_output=True, text=True)


def pipeline(scenario: str, run_id: str, out: Path | None = None) -> Path:
    out = out or APP / "output" / f"{run_id}.json"
    wipe()
    rebuild()
    run([str(BIN), "load", "--scenario", scenario, "--run-id", run_id])
    run([str(BIN), "analyze", "--run-id", run_id])
    run([str(BIN), "emit", "--run-id", run_id, "--output", str(out)])
    return out


def analyze_only(run_id: str) -> None:
    rebuild()
    run([str(BIN), "load", "--scenario", "httpx-pin-requests", "--run-id", run_id])
    run([str(BIN), "analyze", "--run-id", run_id])


def emit_only(run_id: str, out: Path) -> None:
    rebuild()
    run([str(BIN), "emit", "--run-id", run_id, "--output", str(out)])


def load_snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))
