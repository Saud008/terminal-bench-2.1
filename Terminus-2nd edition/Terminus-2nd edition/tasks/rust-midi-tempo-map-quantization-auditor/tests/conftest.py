import subprocess
from pathlib import Path

import pytest

APP = Path("/app")


@pytest.fixture(scope="session", autouse=True)
def rebuild_midgrid():
    proc = subprocess.run(
        ["cargo", "build", "--release", "--locked"],
        cwd=str(APP),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    bin_src = APP / "target" / "release" / "midgrid"
    bin_dst = APP / "bin" / "midgrid"
    bin_dst.parent.mkdir(parents=True, exist_ok=True)
    bin_dst.write_bytes(bin_src.read_bytes())
