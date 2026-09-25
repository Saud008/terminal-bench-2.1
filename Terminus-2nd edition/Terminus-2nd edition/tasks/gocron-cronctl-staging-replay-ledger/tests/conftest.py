"""Verifier session setup: hidden fixtures and cronctl rebuild."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

TEST_DIR = Path(os.environ.get("TEST_DIR", "/tests"))
FIXTURE_SRC = TEST_DIR / "verifier-fixtures"
FIXTURE_DST = Path("/opt/verifier-fixtures")


@pytest.fixture(scope="session", autouse=True)
def _install_hidden_fixtures_and_rebuild() -> None:
    if FIXTURE_SRC.is_dir():
        FIXTURE_DST.mkdir(parents=True, exist_ok=True)
        shutil.copytree(FIXTURE_SRC, FIXTURE_DST, dirs_exist_ok=True)

    env = os.environ.copy()
    subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        cwd="/app",
        check=True,
        env=env,
    )
    subprocess.run(
        [
            "go",
            "build",
            "-mod=readonly",
            "-trimpath",
            "-ldflags=-s -w",
            "-o",
            "/usr/local/bin/cronctl",
            "./cmd/cronctl",
        ],
        cwd="/app",
        check=True,
        env=env,
    )
