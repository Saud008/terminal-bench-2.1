"""Subprocess helpers for pamtrace CLI.

Verifier note: exercises load and emit pipeline stages via subprocess.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "pamtrace"
LEDGER = APP / "state" / "pamtrace-ledger.json"
CONFIG = APP / "config" / "pamtrace.json"


def invoke(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        env=merged,
        cwd=str(APP),
        timeout=120,
        check=False,
    )


def wipe() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True, cwd=str(APP))
    subprocess.run(["bash", str(APP / "scripts" / "rebuild-pamtrace.sh")], check=True, cwd=str(APP))


def run_pipeline(
    scenario: str,
    run_id: str,
    *,
    service: str,
    subject: str,
    scenario_root: Path | None = None,
) -> Path:
    env = {}
    if scenario_root is not None:
        env["PAMTRACE_SCENARIO_OVERRIDE"] = str(scenario_root)
    proc = invoke([str(CLI), "load", "--scenario", scenario, "--run-id", run_id], env=env or None)
    assert proc.returncode == 0, proc.stderr
    proc = invoke([str(CLI), "compile", "--run-id", run_id], env=env or None)
    assert proc.returncode == 0, proc.stderr
    out = APP / "output" / f"{run_id}.json"
    proc = invoke(
        [
            str(CLI),
            "emit",
            "--run-id",
            run_id,
            "--service",
            service,
            "--subject",
            subject,
            "--output",
            str(out),
        ],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr
    return out
