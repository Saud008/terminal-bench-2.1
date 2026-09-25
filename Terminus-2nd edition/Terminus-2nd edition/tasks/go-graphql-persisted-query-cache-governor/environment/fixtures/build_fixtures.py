#!/usr/bin/env python3
"""Build persisted-query manifest fixtures with normalized operation hashes."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN = os.environ.get("PQGOV_HIDDEN_ROOT")


def normalize_query(text: str) -> str:
    return " ".join(text.strip().split())


def operation_hash(query: str) -> str:
    norm = normalize_query(query)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def write_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    q = payload["query_text"]
    payload = dict(payload)
    payload["operation_hash"] = operation_hash(q)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_bundle(base: Path) -> None:
    schemas = {
        "tenants": {
            "acme-corp": {"schema_hash": "gql:acme:v3"},
            "beta-lane": {"schema_hash": "gql:beta:v2"},
            "quota-trap-tenant": {"schema_hash": "gql:trap:v1"},
            "schema-trap-tenant": {"schema_hash": "gql:compound:base"},
        }
    }
    quotas = {
        "tenants": {
            "acme-corp": {"max_active": 5},
            "beta-lane": {"max_active": 2},
            "quota-trap-tenant": {"max_active": 2},
            "schema-trap-tenant": {"max_active": 3},
        }
    }
    expiry = {"ttl_ms": 3_600_000}
    (base / "schemas.json").write_text(json.dumps(schemas, indent=2) + "\n", encoding="utf-8")
    (base / "quotas.json").write_text(json.dumps(quotas, indent=2) + "\n", encoding="utf-8")
    (base / "expiry.json").write_text(json.dumps(expiry, indent=2) + "\n", encoding="utf-8")

    now = 1_700_007_200_000
    ttl = expiry["ttl_ms"]

    clean = [
        {
            "operation_id": "GetUser",
            "schema_hash": "gql:acme:v3",
            "query_text": "query GetUser { user { id name } }",
            "registered_at_ms": now - 7200000,
            "last_seen_ms": now - 1000,
            "manifest_version": 1,
        },
        {
            "operation_id": "ListPosts",
            "schema_hash": "gql:acme:v3",
            "query_text": "query ListPosts { posts { id title } }",
            "registered_at_ms": now - 5400000,
            "last_seen_ms": now - 2000,
            "manifest_version": 1,
        },
    ]
    for row in clean:
        write_manifest(base / "tenants/clean-tenant/manifests" / f"{row['operation_id']}.json", row)

    drift = dict(clean[0])
    drift["schema_hash"] = "gql:wrong:v9"
    write_manifest(base / "tenants/schema-drift/manifests/GetUser.json", drift)

    quota_rows = []
    for i in range(6):
        quota_rows.append(
            {
                "operation_id": f"Op{i+1}",
                "schema_hash": "gql:acme:v3",
                "query_text": f"query Op{i+1} {{ field{i+1} }}",
                "registered_at_ms": now - 8000000 + i * 100000,
                "last_seen_ms": now - 600000 + i * 10000,
                "manifest_version": 1,
            }
        )
    for row in quota_rows:
        write_manifest(base / "tenants/quota-bound/manifests" / f"{row['operation_id']}.json", row)

    stale = dict(clean[0])
    stale["operation_id"] = "StaleQuery"
    stale["last_seen_ms"] = now - ttl - 5000
    write_manifest(base / "tenants/expiry-stale/manifests/StaleQuery.json", stale)

    norm = dict(clean[0])
    norm["operation_id"] = "WhitespaceQuery"
    norm["query_text"] = "  query   GetUser   {   user   {   id   }   }  "
    write_manifest(base / "tenants/hash-normalize/manifests/WhitespaceQuery.json", norm)

    trap_quota = []
    for i, op_id in enumerate(("TrapA", "TrapB", "TrapC")):
        trap_quota.append(
            {
                "operation_id": op_id,
                "schema_hash": "gql:trap:v1",
                "query_text": f"query {op_id} {{ trap{i} }}",
                "registered_at_ms": now - 5000000,
                "last_seen_ms": now - 300000 + i * 50000,
                "manifest_version": 1,
            }
        )
    for row in trap_quota:
        write_manifest(base / "tenants/quota-trap/manifests" / f"{row['operation_id']}.json", row)

    schema_trap = {
        "operation_id": "CompoundQuery",
        "schema_hash": "cmp:schema-trap-tenant:gql:compound:base",
        "query_text": "query CompoundQuery { compound { ok } }",
        "registered_at_ms": now - 1000000,
        "last_seen_ms": now - 1000,
        "manifest_version": 1,
    }
    write_manifest(base / "tenants/schema-trap/manifests/CompoundQuery.json", schema_trap)

    catalog = {
        "scenarios": [
            "clean-tenant",
            "schema-drift",
            "quota-bound",
            "expiry-stale",
            "hash-normalize",
            "quota-trap",
            "schema-trap",
        ],
        "now_ms": now,
    }
    (base / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    build_bundle(ROOT)
    if HIDDEN:
        build_bundle(Path(HIDDEN))


if __name__ == "__main__":
    main()
