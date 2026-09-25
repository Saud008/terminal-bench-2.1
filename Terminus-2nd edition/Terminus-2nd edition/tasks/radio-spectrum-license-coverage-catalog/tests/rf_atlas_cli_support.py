"""CLI helpers for rflicat tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI_BIN = APP_ROOT / "bin" / "rflicat"
RESET_SH = APP_ROOT / "scripts" / "reset-state.sh"
STAGING_PATH = APP_ROOT / "state" / "rf-grant-wal.json"
COVERAGE_PATH = APP_ROOT / "work" / "rf-atlas-generation.json"
FIXTURE_DIR = Path("/opt/rflicat-bundles/bundles")
SEED_POOL = json.loads(Path("/opt/rflicat-bundles/seeds.json").read_text(encoding="utf-8"))["seeds"]


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=merged)


def wipe() -> None:
    proc = invoke(["bash", str(RESET_SH)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(seed: str, bundle: str, *, fixture_dir: Path | None = None, env: dict | None = None) -> Path:
    merged = dict(env or {})
    if fixture_dir is not None:
        merged["TB3_FIXTURE_DIR"] = str(fixture_dir.parent if fixture_dir.name == "bundles" else fixture_dir)
    for step in (
        [str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", bundle],
    ):
        proc = invoke(step, env=merged)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{seed}-{bundle}-catalog.json"
    proc = invoke(
        [str(CLI_BIN), "render-atlas", "--seed", seed, "--bundle", bundle, "--output", str(out)],
        env=merged,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return out
