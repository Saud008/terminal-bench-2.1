"""Session bootstrap for the slsacip verifier suite."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import slsacip_harness as harness

INTERNAL_DIR = harness.APP / "cipkernel"
BACKUP_DIR = Path("/tmp/slsacip-cipkernel-backup")


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_session():
    harness.go_build()
    harness.reset_state()
    yield


@pytest.fixture
def fresh_workspace():
    """Snapshot /app/cipkernel before layer probes; restore after."""
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    shutil.copytree(INTERNAL_DIR, BACKUP_DIR)
    try:
        yield
    finally:
        shutil.rmtree(INTERNAL_DIR)
        shutil.copytree(BACKUP_DIR, INTERNAL_DIR)
        shutil.rmtree(BACKUP_DIR)
        harness.go_build()
        harness.reset_state()
