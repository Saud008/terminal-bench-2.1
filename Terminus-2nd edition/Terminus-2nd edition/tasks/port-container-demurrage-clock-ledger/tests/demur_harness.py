"""Drive demurctl load-yard (yard ingest), run-dwell-ledger, and publish-invoices pipeline."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/demurctl")
FIXTURE_ROOT = Path("/app/fixtures")
HIDDEN_ROOT = Path("/opt/verifier-fixtures/demurctl")
LEDGER_JSON = Path("/app/work/dwell-ledger.json")
INVOICE_JSON = Path("/app/output/demurrage-invoices.json")
YARD_DB = Path("/app/state/yard.db")
CLOCK_PASS = Path("/app/state/clock-pass.json")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")

SCENARIO_DWELL_GATE = "dwell-gate"
SCENARIO_BASIC = "basic-free-time"
SCENARIO_HOLD = "hold-pause-customs"
SCENARIO_PRECEDENCE = "hold-precedence"
SCENARIO_CLOSURE = "closure-skip"
SCENARIO_TIER = "tier-escalation"
SCENARIO_MULTI = "multi-container"
SCENARIO_IDEM = "rerun-stable"


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


def drive_demur_pipeline(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [str(CLI_BIN), "load-yard", "--scenario", scenario, "--fixture-dir", str(root)],
        [str(CLI_BIN), "run-dwell-ledger"],
        [str(CLI_BIN), "publish-invoices"],
    )
    for step in steps:
        proc = invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_clock_pass() -> int:
    if not CLOCK_PASS.is_file():
        return 0
    return int(load_json(CLOCK_PASS)["clock_pass"])


def fetch_staged_dwell_rows() -> list[dict]:
    conn = sqlite3.connect(YARD_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT container_id, eligible_days, free_days_used, demurrage_days,
               tier1_days, tier2_days, tier3_days, total_cents, active_hold, currency
        FROM staged_dwell ORDER BY container_id
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
