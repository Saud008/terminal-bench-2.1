"""Pytest hooks — rebuild rdampctl from current /app sources before verifier tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def rebuild_rdampctl() -> None:
    for folder in ("lattice", "peers", "runloop", "timeline", "reports"):
        for p in Path("/app", folder).glob("rtl_*.rs"):
            p.touch()
    subprocess.run(["rm", "-rf", "/app/target"], check=True)
    subprocess.run(
        ["/usr/local/cargo/bin/cargo", "build", "--release", "--locked"],
        cwd="/app",
        check=True,
    )
    subprocess.run(
        ["cp", "/app/target/release/rdampctl", "/app/bin/rdampctl"],
        check=True,
    )
