"""Shared CLI helpers for tekton-mount-plan verifier tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

CLI = Path("/usr/local/bin/tekton-mount-plan")


def run_cli(stage: str, fixture: Path) -> dict:
    proc = subprocess.run(
        [str(CLI), stage, "--file", str(fixture)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)
