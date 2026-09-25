from __future__ import annotations

import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def rebuild_intakectl():
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
