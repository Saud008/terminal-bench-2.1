"""Shared railpos CLI paths and subprocess helpers."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI_BIN = APP_ROOT / "bin" / "railpos"
RESET_SH = APP_ROOT / "scripts" / "harness" / "reset-state.sh"
TOPO_CACHE_PATH = "/app/var/rail/trackgraph.snapshot"
OUTPUT_DIR = "/app/output"
SNAP_PATH = Path(TOPO_CACHE_PATH)
GEN_PATH = APP_ROOT / "var" / "rail" / "authority.ticket"
FIXTURE_DIR = APP_ROOT / "fixtures" / "scenarios"
SEED_POOL = json.loads((APP_ROOT / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    combined = os.environ.copy()
    if env:
        combined.update(env)
    return subprocess.run(
        cmd,
        cwd=str(APP_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=combined,
    )


def wipe() -> None:
    proc = invoke(["bash", str(RESET_SH)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(seed: str, scenario: str, *, fixture_dir: Path | None = None, env: dict | None = None) -> Path:
    combined = dict(env or {})
    if fixture_dir is not None:
        combined["TB3_SCENARIO_DIR"] = str(fixture_dir.parent)
    for step in (
        [str(CLI_BIN), "compile-trackgraph", "--seed", seed, "--scenario", scenario],
    ):
        proc = invoke(step, env=combined)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{seed}-{scenario}-conflicts.json"
    assert str(out).startswith(OUTPUT_DIR)
    proc = invoke(
        [str(CLI_BIN), "emit-conflicts", "--seed", seed, "--scenario", scenario, "--output", str(out)],
        env=combined,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
