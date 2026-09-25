"""Session fixtures for bgpcut verifier."""
from __future__ import annotations

import pytest
from bgpcut_support import rebuild


@pytest.fixture(scope="session", autouse=True)
def _rebuild_bgpcut_once() -> None:
    rebuild()
