"""Rebuild railpos from current /app sources before pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

for _sub in ("harness", "yard_math", ""):
    _p = f"/app/scripts/{_sub}" if _sub else "/app/scripts"
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture(scope="session", autouse=True)
def _rebuild_railpos() -> None:
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
    src = app / "target" / "release" / "railpos"
    dst = app / "bin" / "railpos"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
