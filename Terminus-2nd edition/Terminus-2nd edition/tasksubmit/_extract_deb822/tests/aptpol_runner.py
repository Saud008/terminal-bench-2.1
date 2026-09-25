from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "debpol"
GRAPH = APP / "state" / "deb822-policy-graph.json"


def wipe() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def invoke(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        args,
        cwd=str(APP),
        env=merged,
        text=True,
        capture_output=True,
        timeout=120,
    )


def build_and_report(
    scenario: str,
    run_id: str,
    *,
    scenario_root: Path | None = None,
) -> Path:
    env: dict[str, str] = {}
    if scenario_root is not None:
        env["TB3_SCENARIO_ROOT"] = str(scenario_root)
    proc = invoke(
        [str(CLI), "build-policy", "--scenario", scenario, "--run-id", run_id],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr
    out = APP / "output" / f"{run_id}-candidates.json"
    proc = invoke(
        [str(CLI), "candidate-report", "--run-id", run_id, "--output", str(out)],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr
    return out
