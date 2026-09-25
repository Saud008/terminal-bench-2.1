"""Subprocess helpers for qqraftctl verifier."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

BIN = "/app/bin/qqraftctl"
CLUSTER = "edge-quorum"
BUNDLED = Path("/app/fixtures")
OFF_CATALOG = Path("/opt/verifier-fixtures/qqraftctl")

PATHS = {
    "staging": Path("/app/state/raft-staging.json"),
    "audit": Path("/app/work/replica-membership-report.json"),
    "ledger": Path("/app/output/committed-queue-state.jsonl"),
    "seal": Path("/app/output/quorum-ledger-seal.json"),
}

INGEST_SCENARIOS = [
    "leader-handoff",
    "term-order-trap",
    "uncommitted-tail",
    "snapshot-truncation",
    "replica-add-same-term",
    "cross-run-idempotent",
]


def wipe_workspace() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def exec_qqraft(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run([BIN, *args], capture_output=True, text=True, env=merged, check=False)


def drive_full_attestation_run(scenario: str, fixture_root: Path = BUNDLED) -> None:
    env = {"TB3_FIXTURE_DIR": str(fixture_root)} if fixture_root != BUNDLED else {}
    for cmd in (
        ["replay-log", "--cluster", CLUSTER, "--scenario", scenario],
        ["merge-snapshot", "--cluster", CLUSTER, "--scenario", scenario]
        if (fixture_root / scenario / "snapshot.json").exists()
        else None,
        ["audit-membership", "--cluster", CLUSTER, "--scenario", scenario],
        ["export-committed", "--cluster", CLUSTER, "--scenario", scenario],
    ):
        if cmd is None:
            continue
        proc = exec_qqraft(cmd, env=env or None)
        assert proc.returncode == 0, proc.stderr


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
