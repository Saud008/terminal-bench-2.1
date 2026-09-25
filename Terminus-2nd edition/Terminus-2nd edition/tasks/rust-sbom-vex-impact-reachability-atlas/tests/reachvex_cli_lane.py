"""SBOM/VEX reachability atlas CLI lane — subprocess only."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

MINIMAL_BUNDLE = Path("/app/data/bundles/minimal/bundle.json")
CHAIN_BUNDLE = Path("/app/data/bundles/chain/bundle.json")
TB3_EXPIRED = Path("/opt/verifier-fixtures/vex-bundles/tb3-expired-waiver/bundle.json")
TB3_DEV_TRAP = Path("/opt/verifier-fixtures/vex-bundles/tb3-dev-edge-trap/bundle.json")
WAIVER_SNAPSHOT = Path("/app/state/waiver-snapshot.json")
EXPOSURE_LEDGER = Path("/app/output/exposure-ledger.json")
VEXATLAS_BIN = "/app/bin/vexatlas"


def reach_lane_spawn_cli(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def reach_lane_reset() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)
    for p in (WAIVER_SNAPSHOT, EXPOSURE_LEDGER):
        if p.exists():
            p.unlink()


def reach_lane_capture_bundle(bundle: Path) -> None:
    reach_lane_spawn_cli([VEXATLAS_BIN, "capture", "--bundle", str(bundle)])


def reach_lane_rollup_ledger(out: Path = EXPOSURE_LEDGER) -> None:
    reach_lane_spawn_cli([VEXATLAS_BIN, "rollup", "--output", str(out)])


def reach_lane_full_pass(bundle: Path) -> None:
    reach_lane_reset()
    reach_lane_capture_bundle(bundle)
    reach_lane_rollup_ledger()


def reach_lane_read_bundle(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
