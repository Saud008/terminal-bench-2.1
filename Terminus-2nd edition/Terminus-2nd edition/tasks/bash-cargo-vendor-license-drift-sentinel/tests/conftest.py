"""Pytest configuration for cargo vendor sentinel verifier."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def cargo_vendor_app_root() -> str:
    return "/app"
