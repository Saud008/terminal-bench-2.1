"""Pytest fixtures for mpiqctl."""
from __future__ import annotations

import pytest

from permit_queue_driver import wipe_state


@pytest.fixture()
def fresh_insp_state():
    wipe_state()
    yield
    wipe_state()
