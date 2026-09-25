"""Rebuild rotrace and provide isolated_swro_profiler fixture for fouling verifier."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _rebuild_rotrace() -> None:
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
    src = app / "target" / "release" / "rotrace"
    dst = app / "bin" / "rotrace"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())


@pytest.fixture
def isolated_swro_profiler() -> None:
    from swro_pipeline_driver import reset_workspace

    reset_workspace()
    yield
    reset_workspace()
