"""Rebuild wtcdctl from current /app sources before pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

if "/app/scripts" not in sys.path:
    sys.path.insert(0, "/app/scripts")


@pytest.fixture(scope="session", autouse=True)
def _rebuild_wtcdctl() -> None:
    app = Path("/app")
    proc = subprocess.run(
        [
            "/usr/local/cargo/bin/cargo",
            "build",
            "--release",
            "--manifest-path",
            str(app / "Cargo.toml"),
        ],
        cwd=str(app),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    src = app / "target" / "release" / "wtcdctl"
    dst = app / "bin" / "wtcdctl"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
