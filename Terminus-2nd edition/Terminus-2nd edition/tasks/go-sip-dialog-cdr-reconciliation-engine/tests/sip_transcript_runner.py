"""Carrier SIP transcript CLI runner for pytest (subprocess only)."""
from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path

CARRIER_BIN = "/app/bin/sipcdrctl"
CARRIER_TENANT = "carrier-east"
FIXTURE_ROOT = Path("/app/fixtures")
TB3_FIXTURE_DIR = Path("/opt/verifier-fixtures/sipcdrctl")

ARTIFACTS = {
    "staging": Path("/app/state/dialog-buffer.json"),
    "billing": Path("/app/work/billing-window-report.json"),
    "sqlite": Path("/app/output/cdr.sqlite"),
    "seal": Path("/app/output/cdr-publish-seal.json"),
}

MANIFEST_SLUGS = [
    "invite-answer-bye",
    "forked-branch-join",
    "cancel-before-200",
    "provisional-only",
    "clock-skew-window",
    "retransmit-storm",
    "cross-run-stable-bytes",
]


def reset_carrier_workspace() -> None:
    subprocess.run(["bash", "/app/scripts/rebuild-sipcdr.sh"], check=True)
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def invoke_sipcdr(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [CARRIER_BIN, *args],
        capture_output=True,
        text=True,
        env=merged,
        check=False,
    )


def run_carrier_pipeline(scenario: str, fixture_root: Path = FIXTURE_ROOT) -> None:
    env = {"TB3_FIXTURE_DIR": str(fixture_root)} if fixture_root != FIXTURE_ROOT else {}
    steps = [
        ["ingest-transcript", "--tenant", CARRIER_TENANT, "--scenario", scenario],
        ["compile-dialogs", "--tenant", CARRIER_TENANT, "--scenario", scenario],
        ["rate-billing", "--tenant", CARRIER_TENANT, "--scenario", scenario],
        ["export-cdr", "--tenant", CARRIER_TENANT, "--scenario", scenario],
    ]
    for step in steps:
        proc = invoke_sipcdr(step, env=env or None)
        assert proc.returncode == 0, proc.stderr


def fetch_sqlite_rows(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    cur = conn.execute(
        "SELECT call_id, branch_key, answer_ts_ms, end_ts_ms, duration_sec, billing_tier, disposition "
        "FROM cdr_rows ORDER BY call_id, branch_key"
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows
