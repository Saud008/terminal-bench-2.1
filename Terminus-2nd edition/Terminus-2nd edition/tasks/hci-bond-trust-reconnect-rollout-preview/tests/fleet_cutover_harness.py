"""CLI process helpers for hciroll fleet cutover verifier tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

APP = Path("/app")
CLI = APP / "bin" / "hciroll"
OVERLAY_FIXTURE_DIR = "/opt/verifier-fixtures/hciroll"
DEFAULT_ATLAS_PATH = "/app/output/hci_reconnect_rollout_atlas.json"


def wipe_run_state() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def invoke(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
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


def run_cutover_preview(
    scenario: str,
    run_id: str,
    output: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    invoke(["scan", "--scenario", scenario, "--run-id", run_id], env=env)
    invoke(["compile", "--run-id", run_id], env=env)
    out = output or DEFAULT_ATLAS_PATH
    invoke(["publish", "--run-id", run_id, "--output", out], env=env)
    return load_json(out)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
