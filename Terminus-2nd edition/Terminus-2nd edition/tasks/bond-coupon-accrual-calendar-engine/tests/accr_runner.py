from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ACCRCTL = "/app/bin/bondacc"
APP = Path("/app")
RESET = APP / "scripts/reset-state.sh"
ATLAS = APP / "output/accrual-atlas.json"
PASS = APP / "state/accrual-pass.json"
DB = APP / "state/accrual.db"
FIX = APP / "fixtures"
HIDDEN = Path("/opt/verifier-fixtures/bondacc")

SCEN_PLAIN = "plain-act360"
SCEN_30360 = "thirt360-semiannual"
SCEN_EX = "ex-coupon-trap"
SCEN_HOL = "holiday-settle"
SCEN_EOM = "eom-schedule"
SCEN_MULTI = "multi-isin"


def run(argv: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(argv, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def flush() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pipeline(scenario: str, fixture_root: Path | None = None, extra_env: dict | None = None) -> None:
    root = fixture_root or FIX
    env: dict[str, str] = {}
    if fixture_root is not None:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [ACCRCTL, "seed-schedules", "--scenario", scenario, "--fixture-dir", str(root)],
        [ACCRCTL, "apply-trades", "--scenario", scenario, "--fixture-dir", str(root)],
        [ACCRCTL, "run-accrual", "--scenario", scenario, "--fixture-dir", str(root)],
        [ACCRCTL, "publish-atlas", "--scenario", scenario, "--fixture-dir", str(root)],
    )
    for argv in steps:
        proc = run(list(argv), env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
