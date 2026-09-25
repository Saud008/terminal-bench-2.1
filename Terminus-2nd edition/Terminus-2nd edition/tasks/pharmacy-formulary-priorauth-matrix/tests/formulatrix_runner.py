from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

FX_BIN = "/app/bin/formulatrix"
FX_APP = Path("/app")
FX_RESET = Path("/app/scripts/reset-state.sh")
FX_ROSTER = Path("/app/state/formulary-roster.json")
FX_GEN = Path("/app/state/refresh-revision.json")
FX_DB = Path("/app/state/formulary.db")
FX_MATRIX = Path("/app/output/formulary-matrix.json")
FX_BUNDLE = FX_APP / "fixtures"
FX_OVERLAY = Path("/opt/verifier-fixtures/formulatrix")

COVERAGE_SCENARIOS = (
    "ndc-normalize",
    "rxnorm-alias",
    "plan-override",
    "step-chain",
    "date-window",
    "sqlite-dual-refresh",
    "matrix-publish",
    "multi-plan",
)


def fx_invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(FX_APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def fx_clean_state() -> None:
    proc = fx_invoke(["bash", str(FX_RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def fx_full_matrix_run(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or FX_BUNDLE
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    for step in (
        [FX_BIN, "load-scenario", "--scenario", scenario, "--fixture-dir", str(root)],
        [FX_BIN, "refresh-db", "--scenario", scenario],
        [FX_BIN, "publish-matrix", "--scenario", scenario],
    ):
        proc = fx_invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def fx_run_overlay_scenario(scenario: str, overlay_root: Path, extra_env: dict | None = None) -> None:
    env = {"TB3_FIXTURE_DIR": str(overlay_root)}
    if extra_env:
        env.update(extra_env)
    for step in (
        [FX_BIN, "load-scenario", "--scenario", scenario, "--fixture-dir", str(overlay_root)],
        [FX_BIN, "refresh-db", "--scenario", scenario],
        [FX_BIN, "publish-matrix", "--scenario", scenario],
    ):
        proc = fx_invoke(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def fx_read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
