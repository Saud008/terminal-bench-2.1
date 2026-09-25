"""Arena duel admit-log CLI runner for pytest (subprocess only)."""
from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path

ARENA_BIN = "/app/bin/duelctl"
ARENA_ID = "arena-north"
FIXTURE_ROOT = Path("/app/fixtures")
TB3_FIXTURE_DIR = Path("/opt/verifier-fixtures/duelctl")

ARTIFACTS = {
    "staging": Path("/app/state/match-buffer.json"),
    "score": Path("/app/work/score-window-report.json"),
    "sqlite": Path("/app/output/match-ledger.sqlite"),
    "seal": Path("/app/output/match-publish-seal.json"),
}

MANIFEST_SLUGS = [
    "challenge-accept-resign",
    "forked-lane-join",
    "forfeit-before-accept",
    "hold-only",
    "clock-skew-window",
    "retransmit-storm",
    "cross-run-stable-bytes",
]


def reset_arena_workspace() -> None:
    subprocess.run(["bash", "/app/scripts/rebuild-duelctl.sh"], check=True)
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def invoke_duelctl(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [ARENA_BIN, *args],
        capture_output=True,
        text=True,
        env=merged,
        check=False,
    )


def run_arena_pipeline(scenario: str, fixture_root: Path = FIXTURE_ROOT) -> None:
    env = {"TB3_FIXTURE_DIR": str(fixture_root)} if fixture_root != FIXTURE_ROOT else {}
    steps = [
        ["admit-log", "--arena", ARENA_ID, "--scenario", scenario],
        ["fold-branches", "--arena", ARENA_ID, "--scenario", scenario],
        ["score-windows", "--arena", ARENA_ID, "--scenario", scenario],
        ["seal-ledger", "--arena", ARENA_ID, "--scenario", scenario],
    ]
    for step in steps:
        proc = invoke_duelctl(step, env=env or None)
        assert proc.returncode == 0, proc.stderr


def fetch_sqlite_rows(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    cur = conn.execute(
        "SELECT duel_id, branch_key, answer_ts_ms, end_ts_ms, duration_sec, score_band, disposition "
        "FROM ledger_rows ORDER BY duel_id, branch_key"
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows
