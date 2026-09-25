"""Shared rtbalctl subprocess helpers."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
RTBAL = APP / "bin" / "rtbalctl"
RESET = APP / "scripts" / "reset-state.sh"
LATCH = APP / "state" / "trial-latch.json"
STAGING = APP / "work" / "enrollment-chronicle.json"
BALANCE = APP / "work" / "balance-run.json"
FIXTURES = APP / "fixtures"
HIDDEN = Path(__file__).resolve().parent / "vfix"


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    combined = os.environ.copy()
    if env:
        combined.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=combined)


def reset() -> None:
    os.environ.pop("TB3_FIXTURE_DIR", None)
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pipeline(trial_id: str, root: Path | None = None, out_name: str | None = None) -> Path:
    fixture_root = root or FIXTURES
    env = {}
    if root is not None:
        env["TB3_FIXTURE_DIR"] = str(root)
    for step in (
        [str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(fixture_root)],
        [str(RTBAL), "accept-log", "--trial", trial_id, "--root", str(fixture_root)],
        [str(RTBAL), "run-balance", "--trial", trial_id, "--root", str(fixture_root)],
    ):
        proc = run(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / (out_name or f"{trial_id}-closure.json")
    proc = run(
        [str(RTBAL), "emit-closure", "--trial", trial_id, "--root", str(fixture_root), "--out", str(out)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
