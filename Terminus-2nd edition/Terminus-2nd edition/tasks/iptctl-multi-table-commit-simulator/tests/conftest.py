"""Session fixtures for iptctl verifier — rebuild CLI before pytest."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

APP = Path("/app")


@pytest.fixture(scope="session", autouse=True)
def _rebuild_iptctl_before_tests() -> None:
    rebuild = "/app/scripts/rebuild-iptctl.sh"
    if Path(rebuild).is_file():
        proc = subprocess.run(
            ["bash", rebuild],
            cwd="/app",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
    assert Path("/app/scripts/iptctl").is_file(), "missing /app/scripts/iptctl"
