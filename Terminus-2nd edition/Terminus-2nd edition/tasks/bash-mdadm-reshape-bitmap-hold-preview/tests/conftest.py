from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _sync_mdreshape() -> None:
    app = Path("/app")
    subprocess.run(["bash", str(app / "scripts" / "rebuild-mdreshape.sh")], check=True)
    (app / "bin" / "mdreshape").chmod(0o755)
