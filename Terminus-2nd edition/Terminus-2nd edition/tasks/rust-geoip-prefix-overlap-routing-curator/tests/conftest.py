"""Rebuild geocur from current /app sources before pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))


@pytest.fixture(scope="session", autouse=True)
def _rebuild_geocur() -> None:
    app = Path("/app")
    proc = subprocess.run(
        [
            "cargo",
            "build",
            "--release",
            "--locked",
            "--manifest-path",
            str(app / "Cargo.toml"),
        ],
        cwd=str(app),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    src = app / "target" / "release" / "geocur"
    dst = app / "bin" / "geocur"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
