"""Session bootstrap for the wavehold rollout hold-preview verifier suite."""

from __future__ import annotations

import pytest

import rollout_preview_support as support


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_session():
    import subprocess

    subprocess.run(["bash", str(support.APP / "scripts" / "rebuild-wavehold.sh")], check=True)
    support.reset_state()
    yield
