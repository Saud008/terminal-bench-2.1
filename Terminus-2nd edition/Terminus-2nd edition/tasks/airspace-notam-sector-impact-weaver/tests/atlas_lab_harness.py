from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ATLAS_BIN = "/app/bin/airclos"
LAB_APP = Path("/app")
LAB_RESET_SCRIPT = "/app/scripts/reset-lab.sh"
CAMPAIGN_BINDING = Path("/app/state/campaign-binding.json")
CHRONO_CLOSURE = Path("/app/state/chronology-closure.json")
CLOSURE_LATTICE = Path("/app/state/closure-lattice.json")
SEAL_EPOCH = Path("/app/state/seal-epoch.json")
CLOSURE_ATLAS = Path("/app/output/impact-closure-atlas.json")
LAB_FIXTURES = LAB_APP / "fixtures"
LAB_HIDDEN = Path("/opt/verifier-fixtures/airclos")

BUNDLED_SCENARIOS = (
    "amend-latest-wins",
    "midnight-window-active",
    "sector-fix-inside",
    "runway-normalize-match",
    "airway-catalog-expand",
    "inactive-window-skip",
    "multi-flight-mixed",
    "stable-repeat-report",
)


def lab_cli(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd="/app", capture_output=True, text=True, check=False, env=merged)


def lab_reset_workspace() -> None:
    subprocess.run(["bash", LAB_RESET_SCRIPT], check=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_closure_pipeline(scenario: str, fixture_dir: Path | None = None) -> None:
    fd = str(fixture_dir or LAB_FIXTURES)
    for cmd in (
        [ATLAS_BIN, "bind-campaign", "--scenario", scenario, "--fixture-dir", fd],
        [ATLAS_BIN, "close-chronology", "--scenario", scenario],
        [ATLAS_BIN, "fold-closure", "--scenario", scenario],
        [ATLAS_BIN, "seal-atlas", "--scenario", scenario],
    ):
        proc = lab_cli(cmd)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr + proc.stdout)
