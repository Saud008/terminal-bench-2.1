import pytest


@pytest.fixture(scope="session", autouse=True)
def _rebuild_filingatlas() -> None:
    import subprocess

    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
