"""CLI and fixture helpers for routeleaklab verifier tests."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

FIXTURES = Path("/app/fixtures/experiments")
HIDDEN = Path("/opt/verifier-fixtures/routeleaklab/experiments")


def reset() -> None:
    subprocess.run(["/app/scripts/reset-state.sh"], check=True)


def rebuild() -> None:
    subprocess.run(["/app/scripts/rebuild-routeleaklab.sh"], check=True)


def evaluate(
    experiment: str,
    report: Path | None = None,
    *,
    run_id: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = ["routeleaklab", "evaluate", "--experiment", experiment]
    if report is not None:
        command.extend(["--report", str(report)])
    if run_id is not None:
        command.extend(["--run-id", run_id])
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(command, text=True, capture_output=True, env=merged_env, check=False)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
