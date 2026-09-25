"""CLI support helpers for mlprov tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI_BIN = Path("/usr/local/bin/mlprov")
RESET_SH = APP_ROOT / "scripts" / "reset-state.sh"
SNAP_PATH = APP_ROOT / "state" / "provenance-staging.json"
DB_PATH = APP_ROOT / "work" / "provenance.db"
FIXTURE_DIR = APP_ROOT / "fixtures" / "scenarios"
SEED_POOL = json.loads((APP_ROOT / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=merged)


def wipe() -> None:
    proc = invoke(["bash", str(RESET_SH)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_curator(seed: str, scenario: str, *, fixture_dir: Path | None = None, env: dict | None = None) -> Path:
    merged = dict(env or {})
    if fixture_dir is not None:
        merged["TB3_FIXTURE_DIR"] = str(fixture_dir)
    for step in (
        [str(CLI_BIN), "ingest", "--seed", seed, "--scenario", scenario],
        [str(CLI_BIN), "curate", "bind", "--seed", seed, "--scenario", scenario],
    ):
        proc = invoke(step, env=merged)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / (seed + "-" + scenario + "-" + "provenance" + ".json")
    proc = invoke(
        [str(CLI_BIN), "export", "summary", "--seed", seed, "--scenario", scenario, "--output", str(out)],
        env=merged,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
