from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _sync_zfshold() -> None:
    app = Path("/app")
    subprocess.run(["bash", str(app / "scripts" / "rebuild-zfshold.sh")], check=True)
    (app / "bin" / "zfshold").chmod(0o755)
