from __future__ import annotations

import pytest

from whslot_driver import wipe_state as _wipe


@pytest.fixture()
def fresh_wsr_yard():
    _wipe()
    yield
