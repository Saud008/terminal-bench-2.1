#!/usr/bin/env python3
"""Pytest harness for calbind three-phase CLI."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI_BIN = APP / "bin" / "calbind"
PACK_DIR = APP / "fixtures" / "cal_runs"
VAULT_PATH = APP / "state" / "intake-vault.json"
REGISTER_PATH = APP / "work" / "calibration-register.db"
REGISTRY = json.loads((APP / "fixtures" / "run_registry.json").read_text(encoding="utf-8"))
BATCH_POOL = REGISTRY["batch_pool"]


def reset_workspace() -> None:
    subprocess.run(["bash", "/app/scripts/reset-workspace.sh"], check=True)


def run_cli(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [str(CLI_BIN), *args],
        capture_output=True,
        text=True,
        env=run_env,
        check=False,
    )


def ingest(batch_id: str, pack: str, env: dict[str, str] | None = None) -> None:
    proc = run_cli(["ingest", "--batch", batch_id, "--pack", pack], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def fuse(batch_id: str, env: dict[str, str] | None = None) -> None:
    proc = run_cli(["fuse", "--batch", batch_id], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def export(batch_id: str, output: Path, env: dict[str, str] | None = None) -> Path:
    proc = run_cli(["export", "--batch", batch_id, "--output", str(output)], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return output


def full_pipeline(batch_id: str, pack: str, output: Path, env: dict[str, str] | None = None) -> Path:
    ingest(batch_id, pack, env=env)
    fuse(batch_id, env=env)
    return export(batch_id, output, env=env)
