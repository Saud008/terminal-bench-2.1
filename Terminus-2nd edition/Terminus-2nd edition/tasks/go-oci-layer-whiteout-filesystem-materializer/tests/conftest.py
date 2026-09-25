"""Rebuild layerfuse and runtime dirs before pytest."""

from __future__ import annotations

import subprocess
from pathlib import Path


def pytest_configure() -> None:
    for rel in ("/app/var/layerfuse", "/app/output"):
        Path(rel).mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["go", "build", "-o", "/usr/local/bin/layerfuse", "./cmd/layerfuse"],
        cwd="/app",
        check=True,
    )
