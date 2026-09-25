"""Harness paths for sublock pytest."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/relayctl")
SNAP_PATH = Path("/app/var/sub/yard.snapshot")
TICKET_PATH = Path("/app/var/sub/loto.ticket")
OUTPUT_DIR = "/app/output"
SEED_POOL = json.loads(Path("/app/fixtures/seeds.json").read_text(encoding="utf-8"))["seeds"]


def wipe() -> None:
    subprocess.run(["bash", "/app/scripts/harness/reset-state.sh"], check=True)


def run_pipeline(
    seed: str,
    scenario: str,
    out_name: str | None = None,
    fixture_dir: Path | None = None,
    env: dict[str, str] | None = None,
) -> Path:
    wipe()
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    if fixture_dir is not None:
        run_env["TB3_SCENARIO_DIR"] = str(fixture_dir.parent)
    subprocess.run(
        [str(CLI_BIN), "compile-yard", "--seed", seed, "--scenario", scenario],
        check=True,
        env=run_env,
    )
    name = out_name or f"{scenario}-verify.json"
    out = Path(OUTPUT_DIR) / name
    subprocess.run(
        [
            str(CLI_BIN),
            "verify-order",
            "--seed",
            seed,
            "--scenario",
            scenario,
            "--output",
            str(out),
        ],
        check=True,
        env=run_env,
    )
    return out


def scenario_dir() -> Path:
    override = os.environ.get("TB3_SCENARIO_DIR")
    if override:
        return Path(override) / "scenarios"
    return Path("/app/fixtures/scenarios")
