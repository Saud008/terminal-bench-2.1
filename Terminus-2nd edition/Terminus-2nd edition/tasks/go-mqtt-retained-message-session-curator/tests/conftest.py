import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def rebuild_mqttsessctl() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert Path("/app/bin/mqttsessctl").is_file()
