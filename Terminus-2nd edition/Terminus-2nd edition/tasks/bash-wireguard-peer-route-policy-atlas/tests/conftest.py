from __future__ import annotations

import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def _rebuild_wgpatlas_once() -> None:
    subprocess.run(["bash", "/app/scripts/rebuild-wgpatlas.sh"], check=True)
