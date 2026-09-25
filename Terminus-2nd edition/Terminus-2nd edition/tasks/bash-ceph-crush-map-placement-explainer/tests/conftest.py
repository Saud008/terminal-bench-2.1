from __future__ import annotations

import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def _rebuild_crpe_once() -> None:
    subprocess.run(["bash", "/app/scripts/rebuild-crpe.sh"], check=True)
