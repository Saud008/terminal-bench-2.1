"""GraphQL persisted-query governor contract verifier suite."""

from __future__ import annotations

import json
import sqlite3

import pytest

from gql_persist_independent import (
    expected_reconcile_summary,
    expected_staging_snapshot,
    fetch_audit_meta,
    fetch_audit_operation_rows,
    sha256_operation_id,
)
from gqlcache_verifier_harness import (
    AUDIT_DB,
    DEFAULT_TENANT,
    LEDGER_DB,
    PUBLIC_FIXTURES,
    REPORT_JSON,
    REVISION_JSON,
    STAGING_JSON,
    current_apq_audit_seq,
    export_audit_sqlite,
    ingest_manifest_bundle,
    reconcile_tenant_ledger,
    run_full_governor_cycle,
    wipe_gqlcache_workspace,
)


@pytest.mark.parametrize(
    "scenario",
    ["clean-tenant", "hash-normalize"],
)
def test_gql_persist_staging_snapshot_matches_reference(scenario: str) -> None:
    """Ingest must write pq-staging.json matching independent staging_digest reference."""
    wipe_gqlcache_workspace()
    proc = ingest_manifest_bundle(DEFAULT_TENANT, scenario, PUBLIC_FIXTURES)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    ref = expected_staging_snapshot(DEFAULT_TENANT, scenario, PUBLIC_FIXTURES)
    assert body["staging_digest"] == ref["staging_digest"]
    if scenario == "clean-tenant":
        assert body == ref


def test_gql_persist_staging_file_is_compact_json() -> None:
    """Staging snapshot on disk must use compact JSON without indented whitespace."""
    wipe_gqlcache_workspace()
    ingest_manifest_bundle(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    raw = STAGING_JSON.read_text(encoding="utf-8")
    assert "\n  " not in raw
    assert raw.endswith("\n")


def test_gql_persist_schema_drift_ingest_nonzero_exit() -> None:
    """Schema drift manifests must fail ingest per schema-hash contract."""
    wipe_gqlcache_workspace()
    proc = ingest_manifest_bundle(DEFAULT_TENANT, "schema-drift", PUBLIC_FIXTURES)
    assert proc.returncode != 0


def test_gql_persist_operation_hash_whitespace_collapse() -> None:
    """Operation hashes must collapse GraphQL whitespace before digesting."""
    noisy = "  query   GetUser   {   user   {   id   }   }  "
    assert sha256_operation_id(noisy) == sha256_operation_id("query GetUser { user { id } }")


def test_gql_persist_reconcile_increments_revision_counter() -> None:
    """Reconcile must advance apq_audit_seq in apq-audit-seq.json."""
    wipe_gqlcache_workspace()
    ingest_manifest_bundle(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    proc = reconcile_tenant_ledger(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert current_apq_audit_seq() >= 1


@pytest.mark.parametrize(
    ("scenario", "field", "value"),
    [
        ("expiry-stale", "evicted_count", 1),
        ("expiry-stale", "active_count", 0),
        ("quota-bound", "active_count", 5),
        ("quota-bound", "evicted_count", 1),
    ],
)
def test_gql_persist_reconcile_report_counters(scenario: str, field: str, value: int) -> None:
    """Reconcile report active and evicted counters must match independent reference math."""
    wipe_gqlcache_workspace()
    ingest_manifest_bundle(DEFAULT_TENANT, scenario, PUBLIC_FIXTURES)
    reconcile_tenant_ledger(DEFAULT_TENANT, scenario, PUBLIC_FIXTURES)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = expected_reconcile_summary(DEFAULT_TENANT, scenario, PUBLIC_FIXTURES, starting_revision=0)
    assert report[field] == ref[field] == value


def test_gql_persist_export_audit_blocked_without_reconcile() -> None:
    """Audit export must refuse when apq_audit_seq is still zero."""
    wipe_gqlcache_workspace()
    ingest_manifest_bundle(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    proc = export_audit_sqlite(DEFAULT_TENANT, "clean-tenant")
    assert proc.returncode != 0


def test_gql_persist_apq_audit_seq_monotonic_on_repeat() -> None:
    """Each reconcile pass must increment apq_audit_seq by exactly one."""
    wipe_gqlcache_workspace()
    ingest_manifest_bundle(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    reconcile_tenant_ledger(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    first = current_apq_audit_seq()
    reconcile_tenant_ledger(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    assert current_apq_audit_seq() == first + 1


def test_gql_persist_audit_meta_matches_reconcile_summary() -> None:
    """Audit export meta table must mirror reconcile report counters."""
    wipe_gqlcache_workspace()
    run_full_governor_cycle(DEFAULT_TENANT, "clean-tenant")
    meta = fetch_audit_meta(AUDIT_DB)
    ref = expected_reconcile_summary(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES, starting_revision=0)
    assert meta["active_count"] == ref["active_count"]
    assert meta["evicted_count"] == ref["evicted_count"]
    assert meta["export_revision"] == current_apq_audit_seq()


def test_gql_persist_audit_rows_mirror_ledger_db() -> None:
    """Audit sqlite operation rows must match pq-ledger.db ledger rows."""
    wipe_gqlcache_workspace()
    run_full_governor_cycle(DEFAULT_TENANT, "quota-bound")
    audit_rows = fetch_audit_operation_rows(AUDIT_DB)
    conn = sqlite3.connect(LEDGER_DB)
    try:
        cur = conn.execute(
            "SELECT operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms FROM pq_operations WHERE tenant_id = ? ORDER BY operation_id",
            (DEFAULT_TENANT,),
        )
        cols = [
            "operation_id",
            "tenant_id",
            "operation_hash",
            "schema_hash",
            "status",
            "registered_at_ms",
            "last_seen_ms",
        ]
        ledger_rows = [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]
    finally:
        conn.close()
    assert audit_rows == ledger_rows


def test_gql_persist_smoke_paths_and_digest() -> None:
    """Bundled ingest must write canonical artifact paths with valid staging_digest."""
    wipe_gqlcache_workspace()
    proc = ingest_manifest_bundle(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    assert proc.returncode == 0
    assert str(STAGING_JSON) == "/app/state/pq-staging.json"
    assert str(REVISION_JSON) == "/app/state/apq-audit-seq.json"
    assert str(LEDGER_DB) == "/app/state/pq-ledger.db"
    body = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    ref = expected_staging_snapshot(DEFAULT_TENANT, "clean-tenant", PUBLIC_FIXTURES)
    assert body["staging_digest"] == ref["staging_digest"]


def test_gql_persist_default_audit_output_path() -> None:
    """Full governor cycle must emit pq-audit.sqlite at the default output path."""
    wipe_gqlcache_workspace()
    out = run_full_governor_cycle(DEFAULT_TENANT, "clean-tenant")
    assert str(out) == "/app/output/pq-audit.sqlite"
    assert AUDIT_DB.is_file()
