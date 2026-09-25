from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _sync_hciroll() -> None:
    app = Path("/app")
    subprocess.run(["bash", str(app / "scripts" / "rebuild-hciroll.sh")], check=True)
    (app / "bin" / "hciroll").chmod(0o755)
