"""Shared subprocess helpers for cronctl ledger verifier."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

APP = Path("/app")
CRONCTL = Path("/usr/local/bin/cronctl")
STAGING = APP / "state" / "replay-snapshot.json"
GENERATION = APP / "state" / "replay-generation.json"
LEDGER_DB = APP / "work" / "ledger.db"
PROBE_FIXTURES = Path("/opt/verifier-fixtures/gocron/scenarios")
# Ground-truth scenarios/seeds live under /tests (verifier-protected), not /app/fixtures.
TEST_DIR = Path(os.environ.get("TEST_DIR", "/tests"))
TRUTH_SCENARIOS = TEST_DIR / "data" / "scenarios"
TRUTH_SEEDS = TEST_DIR / "data" / "seeds.json"


def truth_scenario(name: str) -> Path:
    return TRUTH_SCENARIOS / f"{name}.json"


def _load_seeds() -> list[str]:
    if TRUTH_SEEDS.is_file():
        return json.loads(TRUTH_SEEDS.read_text(encoding="utf-8"))["seeds"]
    return ["alpha", "beta", "gamma"]


SEEDS = _load_seeds()


def invoke_cronctl(
    cmd: list[str], env: dict | None = None
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged
    )


def wipe_replay_state() -> None:
    LEDGER_DB.unlink(missing_ok=True)
    STAGING.unlink(missing_ok=True)
    GENERATION.unlink(missing_ok=True)
    out = APP / "output"
    if out.is_dir():
        for child in out.iterdir():
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
    (APP / "work").mkdir(parents=True, exist_ok=True)
    (APP / "state").mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)


def run_load_replay_export(
    seed: str,
    scenario: str,
    fixture_dir: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> Path:
    env: dict[str, str] = {}
    if fixture_dir is not None:
        env["TB3_FIXTURE_DIR"] = str(fixture_dir)
    if extra_env:
        env.update(extra_env)
    for step in (
        [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario],
        [str(CRONCTL), "replay", "--seed", seed, "--scenario", scenario],
    ):
        proc = invoke_cronctl(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / f"{seed}-{scenario}-ledger.json"
    proc = invoke_cronctl(
        [
            str(CRONCTL),
            "export",
            "--seed",
            seed,
            "--scenario",
            scenario,
            "--output",
            str(out),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
