"""Pytest session hooks — rebuild chmutled before verifier tests."""
from __future__ import annotations

import pytest
from chledger_shell_ops import rebuild_binary


@pytest.fixture(scope="session", autouse=True)
def _session_rebuild() -> None:
    rebuild_binary()
