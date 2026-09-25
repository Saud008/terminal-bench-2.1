"""Independent persisted-query reference for gqlcache governor verifier."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import OrderedDict
from pathlib import Path

FIXTURE_NOW_MS = 1_700_007_200_000


def collapse_graphql_whitespace(text: str) -> str:
    return " ".join(text.strip().split())


def sha256_operation_id(query: str) -> str:
    norm = collapse_graphql_whitespace(query)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_tenant_manifest_rows(fixture_root: Path, scenario: str) -> list[dict]:
    manifest_dir = fixture_root / "tenants" / scenario / "manifests"
    return [_read_json(p) for p in sorted(manifest_dir.glob("*.json"))]


def tenant_schema_hash(tenant_id: str, fixture_root: Path, *, compound: bool = False) -> str:
    base = _read_json(fixture_root / "schemas.json")["tenants"][tenant_id]["schema_hash"]
    if compound:
        return f"cmp:{tenant_id}:{base}"
    return base


def effective_quota_cap(tenant_id: str, fixture_root: Path, quota_bias: int = 0) -> int:
    base = _read_json(fixture_root / "quotas.json")["tenants"][tenant_id]["max_active"]
    return max(0, base + quota_bias)


def policy_ttl_ms(fixture_root: Path, ttl_bias: int = 0) -> int:
    base = int(_read_json(fixture_root / "expiry.json")["ttl_ms"])
    return max(0, base + ttl_bias)


def expected_staging_snapshot(
    tenant_id: str,
    scenario: str,
    fixture_root: Path,
    *,
    compound: bool = False,
) -> dict:
    manifests = load_tenant_manifest_rows(fixture_root, scenario)
    ops = [
        {
            "operation_id": m["operation_id"],
            "operation_hash": sha256_operation_id(m["query_text"]),
            "schema_hash": m["schema_hash"],
            "registered_at_ms": m["registered_at_ms"],
            "last_seen_ms": m["last_seen_ms"],
        }
        for m in manifests
    ]
    ops.sort(key=lambda row: row["operation_id"])
    schema_hash = tenant_schema_hash(tenant_id, fixture_root, compound=compound)
    digest_payload = OrderedDict(
        [
            ("tenant_id", tenant_id),
            ("scenario", scenario),
            ("schema_hash", schema_hash),
            ("operations", ops),
        ]
    )
    digest = hashlib.sha256(json.dumps(digest_payload, separators=(",", ":")).encode()).hexdigest()
    return {
        "engine": "pqgov-v1",
        "tenant_id": tenant_id,
        "scenario": scenario,
        "schema_hash": schema_hash,
        "operation_count": len(ops),
        "operations": ops,
        "staging_digest": digest,
    }


def expected_reconcile_summary(
    tenant_id: str,
    scenario: str,
    fixture_root: Path,
    *,
    now_ms: int = FIXTURE_NOW_MS,
    quota_bias: int = 0,
    ttl_bias: int = 0,
    compound: bool = False,
    starting_revision: int = 0,
) -> dict:
    staging = expected_staging_snapshot(tenant_id, scenario, fixture_root, compound=compound)
    ttl = policy_ttl_ms(fixture_root, ttl_bias)
    cap = effective_quota_cap(tenant_id, fixture_root, quota_bias)
    ledger = [{**op, "tenant_id": tenant_id, "status": "active"} for op in staging["operations"]]
    for row in ledger:
        if now_ms - row["last_seen_ms"] > ttl:
            row["status"] = "evicted"
    active_rows = [r for r in ledger if r["status"] == "active"]
    if len(active_rows) > cap:
        active_rows.sort(key=lambda r: (r["last_seen_ms"], r["operation_id"]))
        drop = {r["operation_id"] for r in active_rows[: len(active_rows) - cap]}
        for row in ledger:
            if row["operation_id"] in drop:
                row["status"] = "evicted"
    active_count = sum(1 for r in ledger if r["status"] == "active")
    evicted_count = sum(1 for r in ledger if r["status"] == "evicted")
    return {
        "tenant_id": tenant_id,
        "scenario": scenario,
        "schema_hash": staging["schema_hash"],
        "active_count": active_count,
        "evicted_count": evicted_count,
        "quota_max": cap,
        "quota_headroom": max(0, cap - active_count),
        "apq_audit_seq": starting_revision + 1,
    }


def fetch_audit_meta(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT tenant_id, scenario, schema_hash, active_count, evicted_count, quota_max, export_revision FROM pq_audit_export_meta"
        ).fetchone()
        assert row is not None
        keys = [
            "tenant_id",
            "scenario",
            "schema_hash",
            "active_count",
            "evicted_count",
            "quota_max",
            "export_revision",
        ]
        return dict(zip(keys, row, strict=True))
    finally:
        conn.close()


def reference_staging_snapshot(
    tenant_id: str,
    scenario: str,
    fixture_root: Path,
    *,
    compound: bool = False,
) -> dict:
    return expected_staging_snapshot(tenant_id, scenario, fixture_root, compound=compound)


def reference_reconcile_report(
    tenant_id: str,
    scenario: str,
    fixture_root: Path,
    *,
    now_ms: int = FIXTURE_NOW_MS,
    quota_bias: int = 0,
    ttl_bias: int = 0,
    compound: bool = False,
    starting_revision: int = 0,
) -> dict:
    return expected_reconcile_summary(
        tenant_id,
        scenario,
        fixture_root,
        now_ms=now_ms,
        quota_bias=quota_bias,
        ttl_bias=ttl_bias,
        compound=compound,
        starting_revision=starting_revision,
    )


def reference_audit_meta(db_path: Path) -> dict:
    return fetch_audit_meta(db_path)


def reference_audit_operations(db_path: Path) -> list[dict]:
    return fetch_audit_operation_rows(db_path)


def fetch_audit_operation_rows(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    try:
        cols = [
            "operation_id",
            "tenant_id",
            "operation_hash",
            "schema_hash",
            "status",
            "registered_at_ms",
            "last_seen_ms",
        ]
        rows = conn.execute(
            "SELECT operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms FROM pq_audit_operations ORDER BY operation_id"
        ).fetchall()
        return [dict(zip(cols, row, strict=True)) for row in rows]
    finally:
        conn.close()
