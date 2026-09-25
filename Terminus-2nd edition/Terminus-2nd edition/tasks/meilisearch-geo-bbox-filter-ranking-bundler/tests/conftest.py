from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _sync_geoboxplay() -> None:
    app = Path("/app")
    subprocess.run(
        ["bash", str(app / "scripts" / "rebuild-geoboxplay.sh")], check=True
    )
    (app / "bin" / "geoboxplay").chmod(0o755)
