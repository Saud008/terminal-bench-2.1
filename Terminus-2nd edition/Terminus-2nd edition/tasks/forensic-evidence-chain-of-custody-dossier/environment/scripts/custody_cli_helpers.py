"""CLI helpers for rvk9 tests."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "rvk9"
RESET = APP / "scripts" / "reset-state.sh"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    combined = os.environ.copy()
    if env:
        combined.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=combined)


def wipe() -> None:
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(case_id: str, bundle: str, *, env: dict | None = None) -> Path:
    combined = dict(env or {})
    out = APP / "output" / f"{case_id}-{bundle}-dossier.json"
    for step in (
        [str(CLI), "vault", "load", "--case", case_id, "--bundle", bundle],
        [str(CLI), "registry", "bind", "--case", case_id, "--bundle", bundle],
        [
            str(CLI),
            "attest",
            "dossier",
            "--case",
            case_id,
            "--bundle",
            bundle,
            "--output",
            str(out),
        ],
    ):
        proc = invoke(step, env=combined)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
