"""CLI helpers for bgpcut verifier."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = Path("/usr/local/bin/bgpcut")
RESET = APP / "scripts" / "reset-state.sh"
REBUILD = APP / "scripts" / "rebuild-bgpcut.sh"
STATE = APP / "state"
FIXTURES = APP / "fixtures" / "peers"
HIDDEN = Path("/opt/verifier-fixtures/bgpcut")


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    assert run(["bash", str(RESET)]).returncode == 0


def rebuild() -> None:
    assert run(["bash", str(REBUILD)]).returncode == 0


def witness(scenario: str, output: Path, run_id: str = "t", *, env=None) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [str(CLI), "cutover", "--scenario", scenario, "--output", str(output), "--run-id", run_id],
        env=env,
    )


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
