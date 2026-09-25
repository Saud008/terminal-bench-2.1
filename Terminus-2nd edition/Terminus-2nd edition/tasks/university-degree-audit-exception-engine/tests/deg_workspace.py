"""Subprocess CLI runner helpers for degaudit verifier scenarios."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/degaudit")
FIXTURE_ROOT = Path("/app/fixtures")
HIDDEN_ROOT = Path("/opt/verifier-fixtures/degaudit")
WORKSPACE_DB = Path("/app/state/registrar-workspace.db")
LOAD_MANIFEST = Path("/app/state/load-manifest.json")
EVAL_PASS = Path("/app/state/evaluation-pass.json")
REQ_EVAL = Path("/app/work/requirement-eval.json")
STAGING_JSON = Path("/app/state/transcript-material.json")
REPORT_JSON = Path("/app/output/degree-audit-report.json")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")

SCENARIO_CLEAN = "clean-audit"
SCENARIO_TRANSFER = "transfer-equiv"
SCENARIO_SUBST = "substitution-active"
SCENARIO_CATALOG = "catalog-year-lock"
SCENARIO_REPEAT = "repeat-retake"
SCENARIO_CLOSURE = "requirement-closure"
SCENARIO_WAIVER = "exception-waiver"
SCENARIO_STABLE = "stable-report"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def wipe_state() -> None:
    proc = invoke(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def execute_degree_audit_workflow(scenario: str, fixture_root: Path | None = None, extra_env: dict | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [str(CLI_BIN), "load-scenario", "--scenario", scenario, "--fixture-dir", str(root)],
        [str(CLI_BIN), "materialize-transcript", "--scenario", scenario],
        [str(CLI_BIN), "run-audit", "--scenario", scenario],
        [str(CLI_BIN), "publish-report", "--scenario", scenario],
    )
    for step in steps:
        proc = invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


run_pipeline = execute_degree_audit_workflow
