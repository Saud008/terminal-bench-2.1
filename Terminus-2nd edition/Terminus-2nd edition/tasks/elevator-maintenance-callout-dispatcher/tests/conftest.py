"""Pytest fixtures for calloutd verifier runs."""
from __future__ import annotations

import pytest

from callout_pipeline import wipe_state as _wipe


@pytest.fixture()
def fresh_callout_state():
    _wipe()
    yield
