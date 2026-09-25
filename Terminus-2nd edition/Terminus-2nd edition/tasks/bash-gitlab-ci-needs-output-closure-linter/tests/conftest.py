"""Sync gclint shell modules before pytest."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _sync_gclint() -> None:
    app = Path("/app")
    subprocess.run(["bash", str(app / "scripts" / "rebuild-gclint.sh")], check=True)
    for sh in (app / "lib" / "gclint").rglob("*.sh"):
        sh.chmod(0o755)
    (app / "bin" / "gclint").chmod(0o755)
