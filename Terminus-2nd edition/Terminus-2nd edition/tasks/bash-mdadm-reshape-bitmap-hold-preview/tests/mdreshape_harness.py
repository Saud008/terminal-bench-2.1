"""CLI helpers for mdreshape verifier tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


APP = Path("/app")
CLI = APP / "bin" / "mdreshape"
HIDDEN_FIXTURE_DIR = "/opt/verifier-fixtures/mdreshape"
DEFAULT_ATLAS_PATH = "/app/output/mdreshape_eligibility_atlas.json"


def reset_state() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def run_cli(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [str(CLI), *args],
        check=True,
        text=True,
        capture_output=True,
        env=merged,
    )


def scan_compile_publish(
    scenario: str,
    run_id: str,
    output: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    run_cli(["scan", "--scenario", scenario, "--run-id", run_id], env=env)
    run_cli(["compile", "--run-id", run_id], env=env)
    out = output or DEFAULT_ATLAS_PATH
    run_cli(["publish", "--run-id", run_id, "--output", out], env=env)
    return json.loads(Path(out).read_text(encoding="utf-8"))


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
