from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _sync_kcfgattest() -> None:
    app = Path("/app")
    subprocess.run(["bash", str(app / "scripts" / "rebuild-kcfgattest.sh")], check=True)
    (app / "bin" / "kcfgattest").chmod(0o755)
