"""Pytest session fixtures for sublock verifier.

Cross-run yard snapshot persistence uses monotonic load_seq sequence counters.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

for _sub in ("harness", "interlock_contract", ""):
    _p = f"/app/scripts/{_sub}" if _sub else "/app/scripts"
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture
def relayctl_bin() -> Path:
    return Path("/app/bin/relayctl")


@pytest.fixture
def seed_pool() -> list[str]:
    return json.loads(Path("/app/fixtures/seeds.json").read_text(encoding="utf-8"))["seeds"]


@pytest.fixture(autouse=True)
def clean_yard_state():
    subprocess.run(["bash", "/app/scripts/harness/reset-state.sh"], check=True)
    yield
    subprocess.run(["bash", "/app/scripts/harness/reset-state.sh"], check=True)
