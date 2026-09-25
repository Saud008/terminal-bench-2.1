"""Whslot CLI driver: latch-yard ingest step through emit-atlas schedule export."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

WHSLOT_BIN = "/app/bin/whslot"
DB_PATH = Path("/app/state/slot-ledger.db")
ATLAS_JSON = Path("/app/output/slot-replen-atlas.json")
FIXTURE_ROOT = Path(os.environ.get("TB3_FIXTURE_DIR", "/app/fixtures"))


def wipe_state() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def invoke(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [WHSLOT_BIN, *args],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )


def run_pipeline(scenario: str, *, fixture_root: Path | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    steps = [
        ["latch-yard", "--scenario", scenario, "--fixture-dir", str(root)],
        ["score-skus"],
        ["draft-wave"],
        ["crew-bind"],
        ["emit-atlas"],
    ]
    for step in steps:
        proc = invoke(step)
        assert proc.returncode == 0, proc.stderr + proc.stdout
