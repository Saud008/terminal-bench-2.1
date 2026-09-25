"""Rebuild minclus from current /app sources before pytest."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _rebuild_minclus() -> None:
    app = Path("/app")
    proc = subprocess.run(
        [
            "/usr/local/cargo/bin/cargo",
            "build",
            "--release",
            "--locked",
            "--manifest-path",
            str(app / "Cargo.toml"),
        ],
        cwd=str(app),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    src = app / "target" / "release" / "minclus"
    dst = app / "bin" / "minclus"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
