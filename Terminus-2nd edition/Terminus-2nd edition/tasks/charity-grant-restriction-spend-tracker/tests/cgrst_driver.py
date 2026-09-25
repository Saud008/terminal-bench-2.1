from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path("/app")
BIN = "/app/bin/grantctl"
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")
FIXTURE_ROOT = ROOT / "fixtures"
HIDDEN_ROOT = Path("/opt/verifier-fixtures/grantctl")
DB_PATH = Path("/app/state/grant-portfolio.db")
PASS_JSON = Path("/app/state/amendment-pass.json")
ATLAS_JSON = Path("/app/output/spend-atlas.json")


def invoke(cmd: list[str], extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def wipe_state() -> None:
    proc = invoke(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(scenario: str, fixture_root: Path | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    steps = (
        [BIN, "load-portfolio", "--scenario", scenario, "--fixture-dir", str(root)],
        [BIN, "apply-amendments"],
        [BIN, "publish-spend-atlas"],
    )
    for step in steps:
        proc = invoke(step)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def read_atlas() -> dict:
    return json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
