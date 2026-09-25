"""Verifier-wide runtime setup."""
from __future__ import annotations

import pytest

from routeleak_support import rebuild


@pytest.fixture(scope="session", autouse=True)
def rebuild_routeleaklab() -> None:
    rebuild()
