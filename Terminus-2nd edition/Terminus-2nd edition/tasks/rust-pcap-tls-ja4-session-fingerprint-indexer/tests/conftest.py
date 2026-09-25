"""Rebuild ja4idx from current /app sources before pytest."""

from __future__ import annotations

import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def _rebuild_ja4idx() -> None:
    proc = subprocess.run(
        ["bash", "/app/environment/scripts/build_all.sh"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
