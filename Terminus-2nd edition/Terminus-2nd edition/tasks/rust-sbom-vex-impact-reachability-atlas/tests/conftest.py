"""Pytest hooks — rebuild vexatlas from current /app sources before verifier tests."""

from __future__ import annotations

import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def rebuild_vexatlas() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)
    subprocess.run(
        ["/usr/local/cargo/bin/cargo", "build", "--release", "--locked"],
        cwd="/app",
        check=True,
    )
    subprocess.run(
        ["cp", "/app/target/release/vexatlas", "/app/bin/vexatlas"],
        check=True,
    )
