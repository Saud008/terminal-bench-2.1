"""Subprocess helpers for mpiqctl pipeline."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

MPIQ_BIN = "/app/bin/mpiqctl"
DB_PATH = Path("/app/state/permit.db")
MANIFEST_JSON = Path("/app/output/permit-queue-manifest.json")
FIXTURE_ROOT = Path(os.environ.get("TB3_FIXTURE_DIR", "/app/fixtures"))


def wipe_state() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def invoke(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [MPIQ_BIN, *args],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )


def run_pipeline(scenario: str, *, fixture_root: Path | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    steps = [
        ["snapshot-load", "--scenario", scenario, "--fixture-dir", str(root)],
        ["compile-policy", "--scenario", scenario],
        ["apply-holds", "--scenario", scenario],
        ["filter-blackouts", "--scenario", scenario],
        ["score-queue", "--scenario", scenario],
        ["bind-inspectors", "--scenario", scenario],
        ["publish-queue", "--scenario", scenario],
    ]
    for step in steps:
        proc = invoke(step)
        assert proc.returncode == 0, proc.stderr + proc.stdout
