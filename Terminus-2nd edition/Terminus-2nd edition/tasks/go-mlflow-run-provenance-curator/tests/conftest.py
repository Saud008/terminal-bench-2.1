"""Rebuild mlprov from current /app sources before pytest."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_GO = Path("/usr/local") / "go" / "bin" / "go"
_OUT = Path("/usr/local") / "bin" / "mlprov"


@pytest.fixture(scope="session", autouse=True)
def _rebuild_mlprov() -> None:
    app = Path("/app")
    env = dict(os.environ)
    go_bin = str(Path("/usr/local") / "go" / "bin")
    env["PATH"] = go_bin + os.pathsep + env.get("PATH", "")
    proc = subprocess.run(
        [
            str(_GO),
            "build",
            "-mod=readonly",
            "-trimpath",
            "-ldflags=-s -w",
            "-o",
            str(_OUT),
            "./cmd/mlprov",
        ],
        cwd=str(app),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
