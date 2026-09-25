"""Pytest session hooks — rebuild flink-skew before verifier tests."""
from __future__ import annotations

import pytest

from flink_skew_shell_ops import rebuild_jar


@pytest.fixture(scope="session", autouse=True)
def _session_rebuild() -> None:
    rebuild_jar()
