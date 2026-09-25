"""CLI helpers for reagentwin tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI_BIN = APP_ROOT / "bin" / "reagentwin"
RESET_SH = APP_ROOT / "scripts" / "reset-workspace.sh"
CORR_DIR = APP_ROOT / "work" / "stability-correlation"
FIXTURE_DIR = APP_ROOT / "fixtures" / "lab_sessions"
SESSION_POOL = json.loads((APP_ROOT / "fixtures" / "session_registry.json").read_text(encoding="utf-8"))["sessions"]


def correlation_path(session_id: str) -> Path:
    return CORR_DIR / f"{session_id}.json"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=run_env)


def wipe() -> None:
    proc = invoke(["bash", str(RESET_SH)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_closure_pipeline(
    session_id: str,
    bundle: str,
    *,
    fixture_dir: Path | None = None,
    env: dict | None = None,
) -> Path:
    run_env = dict(env or {})
    if fixture_dir is not None:
        run_env["TB3_FIXTURE_DIR"] = str(fixture_dir.parent if fixture_dir.name == "lab_sessions" else fixture_dir)
    proc = invoke(
        [str(CLI_BIN), "correlate", "--session", session_id, "--bundle", bundle],
        env=run_env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{session_id}-{bundle}-closure.json"
    proc = invoke(
        [str(CLI_BIN), "publish-closure", "--session", session_id, "--output", str(out)],
        env=run_env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
