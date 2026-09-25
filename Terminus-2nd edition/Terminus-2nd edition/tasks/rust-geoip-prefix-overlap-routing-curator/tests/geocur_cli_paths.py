"""Shared geocur CLI paths and subprocess helpers (verifier-only under /tests)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI_BIN = APP_ROOT / "bin" / "geocur"
RESET_SH = APP_ROOT / "scripts" / "reset-state.sh"
FEED_CACHE_PATH = "/app/state/feed-normalize-cache.json"
OUTPUT_DIR = "/app/output"
SNAP_PATH = Path(FEED_CACHE_PATH)
LEDGER_PATH = APP_ROOT / "work" / "overlap-generation.json"
FIXTURE_DIR = APP_ROOT / "fixtures" / "bundles"
SEED_POOL = json.loads((APP_ROOT / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=run_env)


def wipe() -> None:
    proc = invoke(["bash", str(RESET_SH)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(seed: str, bundle: str, *, fixture_dir: Path | None = None, env: dict | None = None) -> Path:
    run_env = dict(env or {})
    if fixture_dir is not None:
        run_env["TB3_FIXTURE_DIR"] = str(fixture_dir)
    for step in (
        [str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", bundle],
        [str(CLI_BIN), "run-reconcile", "--seed", seed, "--bundle", bundle],
    ):
        proc = invoke(step, env=run_env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{seed}-{bundle}-overlap.json"
    assert str(out).startswith(OUTPUT_DIR)
    proc = invoke(
        [str(CLI_BIN), "emit-overlap", "--seed", seed, "--bundle", bundle, "--output", str(out)],
        env=run_env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
