"""Subprocess helpers for platclosectl laboratory verbs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

BIN = Path("/app/bin/platclosectl")
STATE = Path("/app/state")
WORK = Path("/app/work")
OUTPUT = Path("/app/output")
FIXTURES = Path("/app/fixtures/scenarios")


def reset() -> None:
    subprocess.run(["/app/scripts/reset-state.sh"], check=True)


def run(verb: str, scenario: str, *, output: str | None = None, env: dict | None = None):
    args = [str(BIN), verb, "--scenario", scenario]
    if output:
        args += ["--output", output]
    merged = {**os.environ, **(env or {})}
    return subprocess.run(args, text=True, capture_output=True, env=merged, check=False)


def run_full(scenario: str, *, env: dict | None = None) -> None:
    assert run("hydrate-plates", scenario, env=env).returncode == 0
    assert run("bind-residuals", scenario, env=env).returncode == 0
    assert run("seal-closure", scenario, env=env).returncode == 0


def cert(scenario: str) -> dict:
    path = OUTPUT / f"{scenario}-closure-certificate.json"
    return json.loads(path.read_text(encoding="utf-8"))


def bind_pass() -> int:
    return json.loads((STATE / "bind-pass.json").read_text(encoding="utf-8"))["bind_pass"]
