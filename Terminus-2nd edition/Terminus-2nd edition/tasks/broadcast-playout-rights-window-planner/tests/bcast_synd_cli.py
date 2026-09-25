from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/gridplan")
FIXTURE_ROOT = Path("/app/fixtures")
HIDDEN_ROOT = Path("/opt/verifier-fixtures/gridplan")
ACTIVE_GRID = Path("/app/state/active-grid.json")
STAGING_JSON = Path("/app/state/runway-snapshot.json")
PLAN_JSON = Path("/app/output/syndication-plan.json")
CONFLICT_JSON = Path("/app/output/conflict-report.json")
PLAN_DB = Path("/app/state/syndication-plan.db")
RESET_SCRIPT = Path("/app/scripts/wipe-workspace.sh")

SCENARIO_CLEAN = "clean-playout"
SCENARIO_RIGHTS = "rights-overlap"
SCENARIO_BLACKOUT = "blackout-precedence"
SCENARIO_AD = "ad-marker-preserve"
SCENARIO_FEED = "feed-substitution"
SCENARIO_IDEM = "dedupe-recompile"
SCENARIO_STABLE = "stable-airtime-rank"
SCENARIO_MULTI = "multi-feed-plan"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd="/app", capture_output=True, text=True, check=False, env=merged)


def wipe_state() -> None:
    proc = invoke(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(scenario: str, fixture_root: Path | None = None, extra_env: dict | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [str(CLI_BIN), "import-grid", "--scenario", scenario, "--fixture-dir", str(root)],
        [str(CLI_BIN), "snapshot-runway", "--scenario", scenario],
        [str(CLI_BIN), "compile-windows", "--scenario", scenario],
        [str(CLI_BIN), "syndicate-plan", "--scenario", scenario],
    )
    for step in steps:
        proc = invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def sqlite_row_count(scenario: str) -> int:
    conn = sqlite3.connect(str(PLAN_DB))
    try:
        cur = conn.execute("SELECT COUNT(*) FROM plan_rows WHERE scenario = ?", (scenario,))
        return int(cur.fetchone()[0])
    finally:
        conn.close()
