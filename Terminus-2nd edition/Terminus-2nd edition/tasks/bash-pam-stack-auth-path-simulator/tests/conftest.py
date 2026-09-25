"""Pytest bootstrap — rebuild pamtrace before collection."""

from __future__ import annotations

import subprocess


def pytest_configure(config) -> None:
    subprocess.run(["bash", "/app/scripts/rebuild-pamtrace.sh"], check=True)
