"""Shared rdampctl subprocess helpers for BGP dampening verifier."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
RDAMP = APP / "bin" / "rdampctl"
RESET = APP / "scripts" / "reset-state.sh"
LOCK = APP / "state" / "scenario-lock.json"
LEDGER = APP / "state" / "flap-ledger.json"
RUN_COUNTER = APP / "state" / "run-counter.json"
FIXTURES = APP / "fixtures"
# Hidden fixtures live only under tests/ — never baked into the agent image.
HIDDEN = Path(__file__).resolve().parent / "vfix"


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    combined = os.environ.copy()
    if env:
        combined.update(env)
    return subprocess.run(
        cmd,
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
        env=combined,
    )


def reset() -> None:
    os.environ.pop("TB3_HALF_LIFE_BIAS", None)
    os.environ.pop("TB3_FIXTURE_DIR", None)
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pipeline(scenario: str, root: Path | None = None, out_name: str | None = None) -> Path:
    fixture_root = root or FIXTURES
    env = {}
    if root is not None:
        env["TB3_FIXTURE_DIR"] = str(root)
    for step in (
        [str(RDAMP), "compile-scenario", "--scenario", scenario, "--root", str(fixture_root)],
        [str(RDAMP), "drive-feed", "--scenario", scenario, "--root", str(fixture_root)],
    ):
        proc = run(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / (out_name or f"{scenario}-atlas.jsonl")
    proc = run(
        [
            str(RDAMP),
            "emit-atlas",
            "--scenario",
            scenario,
            "--root",
            str(fixture_root),
            "--out",
            str(out),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


def forecast_pipeline(scenario: str, root: Path | None = None, out_name: str | None = None) -> Path:
    fixture_root = root or FIXTURES
    env = {}
    if root is not None:
        env["TB3_FIXTURE_DIR"] = str(root)
    pipeline(scenario, root=root, out_name=f"{scenario}-atlas.jsonl")
    out = APP / "output" / (out_name or f"{scenario}-rfc.jsonl")
    proc = run(
        [
            str(RDAMP),
            "emit-reuse-forecast",
            "--scenario",
            scenario,
            "--root",
            str(fixture_root),
            "--out",
            str(out),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
