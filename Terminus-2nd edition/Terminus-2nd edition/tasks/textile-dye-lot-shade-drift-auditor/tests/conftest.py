"""Pytest session hooks for shadedrift verifier rebuild."""

from __future__ import annotations

import subprocess


def pytest_sessionstart(session) -> None:
    subprocess.run(["bash", "/app/scripts/rebuild-shadedrift.sh"], check=True)
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)
