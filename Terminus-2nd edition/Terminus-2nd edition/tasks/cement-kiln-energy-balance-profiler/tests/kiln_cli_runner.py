"""Subprocess helpers for kilnbal CLI integration tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
KILNBAL = APP / "bin" / "kilnbal"
FIXTURES = APP / "fixtures" / "kiln-runs"
RESET = APP / "scripts" / "reset-workspace.sh"


def shell(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def reset_workspace() -> None:
    proc = shell(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def scenario_path(name: str, env: dict | None = None) -> Path:
    if env and env.get("TB3_FIXTURE_ROOT"):
        return Path(env["TB3_FIXTURE_ROOT"]) / name
    return FIXTURES / name


def drive_full_kiln_run(
    run_id: str,
    scenario: str,
    *,
    env: dict | None = None,
    cal_table: str = "",
) -> Path:
    root = scenario_path(scenario, env)
    meta = json.loads((root / "kiln.meta.json").read_text(encoding="utf-8"))
    base = [str(KILNBAL)]
    load = base + [
        "load-probes",
        "--run-id",
        run_id,
        "--telemetry",
        str(root / "telemetry.csv"),
    ]
    if cal_table:
        load += ["--cal-table", cal_table]
    assert shell(load, env).returncode == 0
    assert (
        shell(
            base
            + [
                "bind-fuel",
                "--run-id",
                run_id,
                "--fuel",
                str(root / "fuel.csv"),
                "--clinker",
                str(root / "clinker.csv"),
                "--kiln-id",
                meta["kiln_id"],
            ],
            env,
        ).returncode
        == 0
    )
    assert shell(base + ["interpolate-probes", "--run-id", run_id], env).returncode == 0
    assert (
        shell(
            base + ["score-balance", "--run-id", run_id, "--heat-loss", str(root / "heat_loss.json")],
            env,
        ).returncode
        == 0
    )
    out = APP / "output" / f"{run_id}-heat-balance-ledger.json"
    assert shell(base + ["publish-ledger", "--run-id", run_id, "--output", str(out)], env).returncode == 0
    return out
