"""Subprocess helpers for calloutd pipeline."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

CALLOUT_BIN = "/app/bin/calloutd"
DB_PATH = Path("/app/state/callout.db")
ROSTER_JSON = Path("/app/output/callout-roster.json")
FIXTURE_ROOT = Path(os.environ.get("TB3_FIXTURE_DIR", "/app/fixtures"))


def wipe_state() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def invoke(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CALLOUT_BIN, *args],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )


def run_pipeline(scenario: str, *, fixture_root: Path | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    steps = [
        ["load-roster", "--scenario", scenario, "--fixture-dir", str(root)],
        ["rank-faults", "--scenario", scenario],
        ["bind-roster", "--scenario", scenario],
        ["emit-callout", "--scenario", scenario],
    ]
    for step in steps:
        proc = invoke(step)
        assert proc.returncode == 0, proc.stderr + proc.stdout
