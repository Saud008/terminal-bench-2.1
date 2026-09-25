"""CLI harness for irrctl."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
BIN = APP / "bin" / "veldt-cli"
LEDGER = APP / "state" / "moisture-ledger.json"
DEFAULT = APP / "fixtures" / "orchards"


def orchard_root() -> Path:
    root = os.environ.get("ORCHARD_SCENARIO_ROOT")
    return Path(root) if root else DEFAULT


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def rebuild() -> None:
    run(["bash", str(APP / "scripts" / "rebuild-veldt-cli.sh")])


def wipe() -> None:
    run(["bash", str(APP / "scripts" / "reset-state.sh")])


def pipeline(orchard: str, run_id: str, out: Path | None = None) -> Path:
    out = out or APP / "output" / f"{run_id}.json"
    wipe()
    rebuild()
    run([str(BIN), "load-pack", "--orchard", orchard, "--run-id", run_id])
    run([str(BIN), "build-ledger", "--run-id", run_id])
    run([str(BIN), "publish-plan", "--run-id", run_id, "--output", str(out)])
    return out


def load_ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))
