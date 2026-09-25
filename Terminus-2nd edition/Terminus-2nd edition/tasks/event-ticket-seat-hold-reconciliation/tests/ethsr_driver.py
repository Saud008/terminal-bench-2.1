"""Drive venuetixctl ingest (load-venue) and export (publish-status) pipeline."""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

CLI_BIN = Path("/app/bin/venuetixctl")
FIXTURE_ROOT = Path("/app/fixtures")
HIDDEN_ROOT = Path("/opt/verifier-fixtures/venuetixctl")
STAGING_JSON = Path("/app/state/seat-hold-snapshot.json")
SQLITE_OUT = Path("/app/output/venue-seat-ledger.sqlite")
CONFLICT_JSON = Path("/app/output/hold-conflict-atlas.json")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")

SCENARIO_CLEAN = "clean-venue"
SCENARIO_EXPIRY = "expiry-block"
SCENARIO_PAYMENT = "payment-precedence"
SCENARIO_ADJACENCY = "adjacency-gap"
SCENARIO_A11Y = "a11y-reserve"
SCENARIO_STABLE = "stable-ledger"
SCENARIO_MULTI = "multi-section"
SCENARIO_IDEM = "stable-rerun"


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


def drive_ethsr_pipeline(scenario: str, fixture_root: Path | None = None, extra_env: dict | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [str(CLI_BIN), "load-venue", "--scenario", scenario, "--fixture-dir", str(root)],
        [str(CLI_BIN), "snapshot-holds", "--scenario", scenario],
        [str(CLI_BIN), "reconcile-map", "--scenario", scenario],
        [str(CLI_BIN), "publish-status", "--scenario", scenario],
    )
    for step in steps:
        proc = invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_sqlite_seat_rows() -> list[dict]:
    conn = sqlite3.connect(SQLITE_OUT)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT seat_id, hold_id, order_id, status FROM seat_status ORDER BY seat_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]
