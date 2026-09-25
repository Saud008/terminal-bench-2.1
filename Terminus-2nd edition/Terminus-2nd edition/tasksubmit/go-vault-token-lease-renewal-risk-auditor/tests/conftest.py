"""Pytest session hooks — rebuild vaultaud before verifier tests."""
from __future__ import annotations

import pytest
from vaultaud_cli import compile_vaultaud


@pytest.fixture(scope="session", autouse=True)
def _compile_vaultaud_once() -> None:
    compile_vaultaud()
