from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _rebuild_k7cal() -> None:
    app = Path("/app")
    subprocess.run(["bash", str(app / "scripts" / "rebuild-k7cal.sh")], check=True)
    (app / "bin" / "k7cal").chmod(0o755)
