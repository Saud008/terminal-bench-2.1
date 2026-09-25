"""Pytest fixtures for renewable PPA settlement verifier runs."""

from __future__ import annotations

import pytest

from ppa_ctl_exec import reset_ppa_workspace


@pytest.fixture(autouse=True)
def _isolate_ppa_state() -> None:
    reset_ppa_workspace()
    yield
    reset_ppa_workspace()
