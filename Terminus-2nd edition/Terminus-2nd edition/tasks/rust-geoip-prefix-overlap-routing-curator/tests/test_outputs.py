"""geocur binary smoke checks."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_geocur_binary_installed():
    """geocur must be installed at /app/bin/geocur per instruction."""
    assert Path("/app/bin/geocur").exists()


def test_geocur_cli_requires_subcommand():
    """geocur must reject invocations without a subcommand."""
    proc = subprocess.run(["/app/bin/geocur"], capture_output=True, text=True, check=False)
    assert proc.returncode != 0
