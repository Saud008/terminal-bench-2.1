from __future__ import annotations

import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def rebuild_wrapper() -> None:
    subprocess.run(["bash", "/app/scripts/verifier-rebuild.sh"], check=True)
