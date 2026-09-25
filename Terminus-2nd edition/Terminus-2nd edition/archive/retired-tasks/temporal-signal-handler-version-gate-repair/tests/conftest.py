"""Pytest fixtures for temporal-signal-replay verifier setup."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
CLI = "/usr/local/bin/temporal-signal-replay"
RESET = APP / "scripts/reset-state.sh"
TESTS = Path(__file__).resolve().parent


@pytest.fixture(scope="session", autouse=True)
def verifier_test_environment() -> None:
    os.environ["PATH"] = (
        "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:"
        + os.environ.get("PATH", "")
    )
    os.environ["PYTHONPATH"] = f"{TESTS}:{os.environ.get('PYTHONPATH', '')}"
    assert Path(CLI).is_file(), f"missing CLI at {CLI}"


@pytest.fixture(autouse=True)
def reset_replay_state() -> None:
    subprocess.run(["bash", str(RESET)], check=True, cwd=str(APP))
    proc = subprocess.run(
        ["go", "build", "-mod=readonly", "-o", CLI, "./cmd/temporal-signal-replay"],
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
