import subprocess
import sys
from pathlib import Path

import pytest

# Reference math and CLI helpers ship under /app/fixtures (solver-visible).
sys.path.insert(0, "/app/fixtures")


@pytest.fixture(scope="session", autouse=True)
def rebuild_wfhistctl() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert Path("/app/bin/wfhistctl").is_file()
