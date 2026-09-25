"""Pytest fixtures for registrar degree audit verifier scenarios."""

from __future__ import annotations

import subprocess

import pytest

from deg_workspace import wipe_state


@pytest.fixture(scope="session", autouse=True)
def _rebuild_degaudit_binary():
    """Rebuild degaudit from /app sources before verifier pytest (compiled stack contract)."""
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        cwd="/app",
        check=False,
    )
    assert proc.returncode == 0, "verifier-rebuild.sh failed"


@pytest.fixture(autouse=True)
def _isolate_registrar_state():
    """Reset /app/state, /app/work, and /app/output before each test."""
    wipe_state()
    yield
    wipe_state()


@pytest.fixture
def bundled_scenarios() -> tuple[str, ...]:
    """Bundled SQLite scenario slugs under /app/fixtures."""
    return (
        "clean-audit",
        "transfer-equiv",
        "substitution-active",
        "catalog-year-lock",
        "repeat-retake",
        "requirement-closure",
        "exception-waiver",
        "stable-report",
    )
