import subprocess

import pytest

AGENT_USER = "agent"


@pytest.fixture(scope="session", autouse=True)
def _rebuild_iceexpctl() -> None:
    # Agent-authored Go sources and the rebuilt binary must not execute as the
    # reward-writing root verifier UID.
    proc = subprocess.run(
        ["runuser", "-u", AGENT_USER, "--", "bash", "/app/scripts/verifier-rebuild.sh"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
