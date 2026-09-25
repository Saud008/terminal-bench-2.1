"""Hidden verifier traps for gqlcache governor TB3 fixtures."""

from __future__ import annotations

import json

from gql_persist_independent import (
    expected_reconcile_summary,
    expected_staging_snapshot,
    fetch_audit_meta,
)
from gqlcache_verifier_harness import (
    AUDIT_DB,
    HIDDEN_FIXTURES,
    PUBLIC_FIXTURES,
    REPORT_JSON,
    STAGING_JSON,
    current_apq_audit_seq,
    ingest_manifest_bundle,
    reconcile_tenant_ledger,
    run_full_governor_cycle,
    wipe_gqlcache_workspace,
)


class TestGqlcacheHiddenQuotaTrap:
    def test_gql_hidden_quota_bias_tightens_cap(self) -> None:
        """TB3_QUOTA_BIAS must tighten hidden tenant max_active during reconcile."""
        wipe_gqlcache_workspace()
        env = {"TB3_QUOTA_BIAS": "-1"}
        ingest_manifest_bundle("quota-trap-tenant", "quota-trap", HIDDEN_FIXTURES, env)
        reconcile_tenant_ledger("quota-trap-tenant", "quota-trap", HIDDEN_FIXTURES, env)
        ref = expected_reconcile_summary(
            "quota-trap-tenant",
            "quota-trap",
            HIDDEN_FIXTURES,
            quota_bias=-1,
            starting_revision=0,
        )
        body = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        assert body["active_count"] == ref["active_count"] == 1
        assert body["evicted_count"] == ref["evicted_count"] == 2


class TestGqlcacheCompoundSchemaTrap:
    def test_gql_hidden_compound_schema_staging(self) -> None:
        """TB3_COMPOUND_SCHEMA must rewrite staging schema_hash for hidden trap tenant."""
        wipe_gqlcache_workspace()
        env = {"TB3_COMPOUND_SCHEMA": "1"}
        proc = ingest_manifest_bundle("schema-trap-tenant", "schema-trap", HIDDEN_FIXTURES, env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        body = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
        ref = expected_staging_snapshot(
            "schema-trap-tenant",
            "schema-trap",
            HIDDEN_FIXTURES,
            compound=True,
        )
        assert body["schema_hash"] == ref["schema_hash"]
        assert body["staging_digest"] == ref["staging_digest"]

    def test_gql_hidden_compound_schema_audit_export(self) -> None:
        """Compound schema trap must survive ingest through audit sqlite export."""
        wipe_gqlcache_workspace()
        env = {"TB3_COMPOUND_SCHEMA": "1"}
        run_full_governor_cycle("schema-trap-tenant", "schema-trap", HIDDEN_FIXTURES, extra_env=env)
        meta = fetch_audit_meta(AUDIT_DB)
        assert meta["tenant_id"] == "schema-trap-tenant"
        assert meta["active_count"] == 1


class TestGqlcacheArtifactPaths:
    def test_gql_tb3_staging_artifact_location(self) -> None:
        """Ingest must materialize pq-staging.json on disk for bundled scenarios."""
        wipe_gqlcache_workspace()
        proc = ingest_manifest_bundle("quota-trap-tenant", "quota-trap", PUBLIC_FIXTURES)
        assert proc.returncode == 0
        assert STAGING_JSON.is_file()

    def test_gql_tb3_revision_gate_after_reconcile(self) -> None:
        """Reconcile must leave apq_audit_seq positive before audit export is allowed."""
        wipe_gqlcache_workspace()
        run_full_governor_cycle("quota-trap-tenant", "quota-trap", fixture_root=PUBLIC_FIXTURES)
        assert current_apq_audit_seq() >= 1
