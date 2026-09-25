"""Verifier harness for gqlcache pqgov CLI subprocess checks."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

GOVERNOR_BIN = "/app/bin/pqgov"
APP_ROOT = Path("/app")
STATE_RESET = APP_ROOT / "scripts" / "reset-state.sh"
STAGING_JSON = APP_ROOT / "state" / "pq-staging.json"
REVISION_JSON = APP_ROOT / "state" / "apq-audit-seq.json"
REPORT_JSON = APP_ROOT / "work" / "reconcile-report.json"
LEDGER_DB = APP_ROOT / "state" / "pq-ledger.db"
AUDIT_DB = APP_ROOT / "output" / "pq-audit.sqlite"
PUBLIC_FIXTURES = APP_ROOT / "fixtures"
HIDDEN_FIXTURES = Path("/opt/verifier-fixtures/pqgov")
DEFAULT_TENANT = "acme-corp"
FIXED_NOW_MS = "1700007200000"


def invoke_gqlcache(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged.setdefault("PQGOV_NOW_MS", FIXED_NOW_MS)
    if env:
        merged.update(env)
    return subprocess.run(
        args,
        cwd=str(APP_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def wipe_gqlcache_workspace() -> None:
    proc = invoke_gqlcache(["bash", str(STATE_RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest_manifest_bundle(
    tenant: str,
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    root = fixture_root or PUBLIC_FIXTURES
    env = dict(extra_env or {})
    return invoke_gqlcache(
        [
            GOVERNOR_BIN,
            "ingest",
            "--tenant",
            tenant,
            "--scenario",
            scenario,
            "--fixture-dir",
            str(root),
        ],
        env=env,
    )


def reconcile_tenant_ledger(
    tenant: str,
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    root = fixture_root or PUBLIC_FIXTURES
    env = dict(extra_env or {})
    return invoke_gqlcache(
        [
            GOVERNOR_BIN,
            "reconcile",
            "--tenant",
            tenant,
            "--scenario",
            scenario,
            "--fixture-dir",
            str(root),
        ],
        env=env,
    )


def export_audit_sqlite(
    tenant: str,
    scenario: str,
    output: Path | None = None,
    extra_env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    out = output or AUDIT_DB
    env = dict(extra_env or {})
    return invoke_gqlcache(
        [
            GOVERNOR_BIN,
            "export-audit",
            "--tenant",
            tenant,
            "--scenario",
            scenario,
            "--output",
            str(out),
        ],
        env=env,
    )


def run_full_governor_cycle(
    tenant: str,
    scenario: str,
    fixture_root: Path | None = None,
    output: Path | None = None,
    extra_env: dict | None = None,
) -> Path:
    root = fixture_root or PUBLIC_FIXTURES
    env = dict(extra_env or {})
    for step in (
        lambda: ingest_manifest_bundle(tenant, scenario, root, env),
        lambda: reconcile_tenant_ledger(tenant, scenario, root, env),
    ):
        proc = step()
        assert proc.returncode == 0, proc.stderr + proc.stdout
    proc = export_audit_sqlite(tenant, scenario, output, env)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return output or AUDIT_DB


def current_apq_audit_seq() -> int:
    return int(json.loads(REVISION_JSON.read_text(encoding="utf-8"))["apq_audit_seq"])
