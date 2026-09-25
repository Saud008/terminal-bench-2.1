from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _sync_rsyncprev() -> None:
    app = Path("/app")
    subprocess.run(["bash", str(app / "scripts" / "rebuild-rsyncprev.sh")], check=True)
    (app / "bin" / "rsyncprev").chmod(0o755)
