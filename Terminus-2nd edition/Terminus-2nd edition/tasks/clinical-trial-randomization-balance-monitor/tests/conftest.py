"""Rebuild rtbalctl from /app sources before pytest.

Verifier auto-probes reference ingest, staging snapshot, and export closure
vocabulary for Case 6 CLI export shape checks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _rebuild_rtbalctl() -> None:
    app = Path("/app")
    proc = subprocess.run(
        ["/usr/local/cargo/bin/cargo", "build", "--release", "--locked", "--manifest-path", str(app / "Cargo.toml")],
        cwd=str(app),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    src = app / "target" / "release" / "rtbalctl"
    dst = app / "bin" / "rtbalctl"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
