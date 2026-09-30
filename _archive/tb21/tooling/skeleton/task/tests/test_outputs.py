"""<<REPLACE: what this suite validates>>"""

import subprocess


def run_app(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/usr/local/go/bin/go", "run", ".", *args],
        cwd="/app",
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_replace_me():
    """<<REPLACE: the behavior this test verifies>>"""
    result = run_app()
    assert result.returncode == 0, f"expected exit 0, got {result.returncode}: {result.stderr}"
