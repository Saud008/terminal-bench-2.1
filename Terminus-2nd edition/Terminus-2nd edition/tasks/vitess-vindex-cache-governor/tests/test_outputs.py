"""
Behavioral verifier for vtgatesim vindex cache and scatter routing.

Independent reference_* helpers mirror /app/docs/ without importing Go code.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
CLI = "/usr/local/bin/vtgatesim"
SNAPSHOT = Path("/app/state/vindex-snapshot.json")
PLAN = Path("/app/output/route-plan.json")
AUDIT = Path("/app/output/routing-audit.json")
RESET = APP / "scripts/reset-state.sh"
FIX = APP / "fixtures"
TB3_ROOT = Path(os.environ.get("TB3_VINDEX_FIXTURES", "/opt/verifier-fixtures"))


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


def _fnv1a64(data: bytes) -> int:
    offset = 14695981039346656037
    prime = 1099511628211
    h = offset
    for b in data:
        h ^= b
        h = (h * prime) & 0xFFFFFFFFFFFFFFFF
    return h


def typed_key_hex(vtype: str, key: str) -> str:
    digest = _fnv1a64(key.encode("utf-8"))
    return f"{vtype}:{digest:016x}"


def space_key(vtype: str, key: str, params: dict[str, str]) -> int:
    """Map vindex key to uint64 routing space per vindex-contract.md."""
    if vtype == "hash":
        return _fnv1a64(key.encode("utf-8"))
    if vtype == "binary":
        raw = bytes.fromhex(key.lower().removeprefix("0x"))
        buf = bytearray(8)
        tail = raw[-8:] if len(raw) > 8 else raw
        buf[8 - len(tail) :] = tail
        return int.from_bytes(buf, "big")
    if vtype == "lookup":
        if key not in params:
            return 0
        shard = params[key]
        return _fnv1a64(shard.encode("utf-8"))
    raise ValueError(f"unknown vindex type {vtype}")


def resolve_shard(space: int, shard_map: dict) -> str:
    shards = shard_map["shards"]
    for sh in shards:
        lo = int(sh["key_range"]["start"], 16)
        hi = int(sh["key_range"]["end"], 16)
        if lo <= space < hi:
            return sh["name"]
    return shards[-1]["name"] if shards else ""


def reference_routes(shard_map_path: Path, catalog_path: Path, batch_path: Path) -> list[dict]:
    """Compute expected routes ignoring cache and scatter simulation."""
    sm = json.loads(shard_map_path.read_text(encoding="utf-8"))
    cat = json.loads(catalog_path.read_text(encoding="utf-8"))
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    defs = {v["name"]: v for v in cat["vindexes"]}
    out: list[dict] = []
    for q in batch["queries"]:
        vname = q["vindex"]
        vdef = defs[vname]
        space = space_key(vdef["type"], q["key"], vdef.get("params", {}))
        shard = resolve_shard(space, sm)
        out.append({"vindex": vname, "key": q["key"], "shard": shard})
    return out


def scatter_should_fail(vtype: str, key: str) -> bool:
    return vtype == "binary" and key.lower().endswith("ff")


def _ingest_base(cache_seed: Path | None = None, shard_map: Path | None = None) -> None:
    cmd = [
        CLI,
        "ingest",
        "--shard-map",
        str(shard_map or FIX / "shardmaps/base-gen1.json"),
        "--vindexes",
        str(FIX / "vindexes/catalog.json"),
        "--snapshot",
        str(SNAPSHOT),
    ]
    if cache_seed is not None:
        cmd.extend(["--cache-seed", str(cache_seed)])
    _run(cmd)


def _route_batch(batch_path: Path) -> dict:
    _run(
        [
            CLI,
            "route",
            "--snapshot",
            str(SNAPSHOT),
            "--batch",
            str(batch_path),
            "--output",
            str(PLAN),
        ]
    )
    return json.loads(PLAN.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_workspace():
    """Reset output/state and rebuild CLI before each test."""
    _run(["bash", str(RESET)])
    _run(["bash", str(APP / "scripts/verifier-rebuild.sh")])


def test_snapshot_written_after_ingest():
    """Ingest must create the staging snapshot artifact documented in revision-snapshot.md."""
    _run(
        [
            CLI,
            "ingest",
            "--shard-map",
            str(FIX / "shardmaps/base-gen1.json"),
            "--vindexes",
            str(FIX / "vindexes/catalog.json"),
            "--snapshot",
            str(SNAPSHOT),
        ]
    )
    assert SNAPSHOT.is_file()
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["generation"] == 1
    assert snap["shard_map_path"] == str(FIX / "shardmaps/base-gen1.json")
    assert len(snap["vindexes"]) == 3


def test_mixed_batch_routes_match_reference():
    """Route plan shards must match independent vindex reference for bundled mixed batch."""
    _run(
        [
            CLI,
            "ingest",
            "--shard-map",
            str(FIX / "shardmaps/base-gen1.json"),
            "--vindexes",
            str(FIX / "vindexes/catalog.json"),
            "--snapshot",
            str(SNAPSHOT),
        ]
    )
    _run(
        [
            CLI,
            "route",
            "--snapshot",
            str(SNAPSHOT),
            "--batch",
            str(FIX / "batches/mixed-types.json"),
            "--output",
            str(PLAN),
        ]
    )
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    expected = reference_routes(
        FIX / "shardmaps/base-gen1.json",
        FIX / "vindexes/catalog.json",
        FIX / "batches/mixed-types.json",
    )
    assert plan["scatter_ok"] is True
    assert len(plan["routes"]) == len(expected)
    for got, want in zip(plan["routes"], expected, strict=True):
        assert got["vindex"] == want["vindex"]
        assert got["key"] == want["key"]
        assert got["shard"] == want["shard"]


def test_binary_padding_uses_uint64_space():
    """Binary vindex must right-pad into eight-byte big-endian space before range lookup."""
    _run(
        [
            CLI,
            "ingest",
            "--shard-map",
            str(FIX / "shardmaps/base-gen1.json"),
            "--vindexes",
            str(FIX / "vindexes/catalog.json"),
            "--snapshot",
            str(SNAPSHOT),
        ]
    )
    batch = {"queries": [{"vindex": "order_binary", "key": "0x00000000000000ab"}]}
    batch_path = APP / "output/padding-batch.json"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    _run(
        [
            CLI,
            "route",
            "--snapshot",
            str(SNAPSHOT),
            "--batch",
            str(batch_path),
            "--output",
            str(PLAN),
        ]
    )
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    want = reference_routes(
        FIX / "shardmaps/base-gen1.json",
        FIX / "vindexes/catalog.json",
        batch_path,
    )[0]["shard"]
    assert plan["routes"][0]["shard"] == want


def test_coalesce_drops_foreign_generation_entries():
    """Ingest coalesce must drop cache rows from other shard-map generations."""
    _run(
        [
            CLI,
            "ingest",
            "--shard-map",
            str(FIX / "shardmaps/base-gen1.json"),
            "--vindexes",
            str(FIX / "vindexes/catalog.json"),
            "--snapshot",
            str(SNAPSHOT),
            "--cache-seed",
            str(FIX / "cache-seed/stale-gen2.json"),
        ]
    )
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap.get("coalesce_dropped", 0) >= 1
    assert snap["cache"] == [] or len(snap["cache"]) == 0


def test_scatter_partial_failure_not_masked_by_cache():
    """Partial scatter faults must error, must not return stale cache, and export scatter_failures."""
    _run(
        [
            CLI,
            "ingest",
            "--shard-map",
            str(FIX / "shardmaps/base-gen1.json"),
            "--vindexes",
            str(FIX / "vindexes/catalog.json"),
            "--snapshot",
            str(SNAPSHOT),
            "--cache-seed",
            str(FIX / "cache-seed/stale-gen2.json"),
        ]
    )
    _run(
        [
            CLI,
            "route",
            "--snapshot",
            str(SNAPSHOT),
            "--batch",
            str(FIX / "batches/scatter-trap.json"),
            "--output",
            str(PLAN),
        ]
    )
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    assert plan["scatter_ok"] is False
    assert plan["routes"] == []
    _run(
        [
            CLI,
            "export",
            "--snapshot",
            str(SNAPSHOT),
            "--plan",
            str(PLAN),
            "--audit-out",
            str(AUDIT),
        ]
    )
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert audit["scatter_failures"] >= 1


def test_rollback_migration_flushes_warm_cache():
    """Rollback must flush cache so generation-2 warm entries cannot affect gen-1 routing."""
    _run(
        [
            CLI,
            "ingest",
            "--shard-map",
            str(FIX / "shardmaps/base-gen1.json"),
            "--vindexes",
            str(FIX / "vindexes/catalog.json"),
            "--snapshot",
            str(SNAPSHOT),
        ]
    )
    _run(
        [
            CLI,
            "migrate",
            "--events",
            str(FIX / "events/rollback-warm.jsonl"),
            "--snapshot",
            str(SNAPSHOT),
        ]
    )
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["generation"] == 1
    assert snap["cache"] == []
    _run(
        [
            CLI,
            "route",
            "--snapshot",
            str(SNAPSHOT),
            "--batch",
            str(FIX / "batches/mixed-types.json"),
            "--output",
            str(PLAN),
        ]
    )
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    expected = reference_routes(
        FIX / "shardmaps/rollback-gen1.json",
        FIX / "vindexes/catalog.json",
        FIX / "batches/mixed-types.json",
    )
    for got, want in zip(plan["routes"], expected, strict=True):
        assert got["shard"] == want["shard"]


def test_export_audit_matches_plan_and_snapshot():
    """Export audit must reflect snapshot generation, coalesce_dropped, and route counts."""
    _run(
        [
            CLI,
            "ingest",
            "--shard-map",
            str(FIX / "shardmaps/base-gen1.json"),
            "--vindexes",
            str(FIX / "vindexes/catalog.json"),
            "--snapshot",
            str(SNAPSHOT),
            "--cache-seed",
            str(FIX / "cache-seed/stale-gen2.json"),
        ]
    )
    _run(
        [
            CLI,
            "route",
            "--snapshot",
            str(SNAPSHOT),
            "--batch",
            str(FIX / "batches/mixed-types.json"),
            "--output",
            str(PLAN),
        ]
    )
    _run(
        [
            CLI,
            "export",
            "--snapshot",
            str(SNAPSHOT),
            "--plan",
            str(PLAN),
            "--audit-out",
            str(AUDIT),
        ]
    )
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert audit["generation"] == snap["generation"]
    assert snap.get("coalesce_dropped", 0) >= 1
    assert audit["coalesce_dropped"] == snap["coalesce_dropped"]
    assert audit["route_count"] == len(plan["routes"])
    assert audit["cache_hit_count"] == plan["cache_hits"]
    assert audit["scatter_failures"] == 0
    assert sum(audit["shard_counts"].values()) == audit["route_count"]


@pytest.mark.skipif(not TB3_ROOT.is_dir(), reason="hidden fixtures only in image")
def test_hidden_type_collision_routes_independently():
    """Hidden batch requires typed cache keys so hash and lookup with same display key diverge."""
    hidden_map = TB3_ROOT / "TB3_shardmaps/hidden-gen3.json"
    batch = TB3_ROOT / "TB3_batches/type-collision.json"
    _run(
        [
            CLI,
            "ingest",
            "--shard-map",
            str(hidden_map),
            "--vindexes",
            str(FIX / "vindexes/catalog.json"),
            "--snapshot",
            str(SNAPSHOT),
        ]
    )
    _run(
        [
            CLI,
            "route",
            "--snapshot",
            str(SNAPSHOT),
            "--batch",
            str(batch),
            "--output",
            str(PLAN),
        ]
    )
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    expected = reference_routes(hidden_map, FIX / "vindexes/catalog.json", batch)
    pairs = {(r["vindex"], r["key"]): r["shard"] for r in plan["routes"]}
    for want in expected:
        assert pairs[(want["vindex"], want["key"])] == want["shard"]
    assert pairs[("user_hash", "TB3_COLLISION_A")] != pairs[
        ("customer_lookup", "TB3_COLLISION_A")
    ]


def test_typed_cache_key_format_reference():
    """Typed cache key helper must match vindex-contract.md (not wrap.go-only hashing)."""
    assert typed_key_hex("user_hash", "alice") != typed_key_hex("customer_lookup", "alice")


def test_snapshot_arrays_never_null():
    """revision-snapshot.md requires vindexes and cache serialize as JSON arrays, never null."""
    _ingest_base()
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert isinstance(snap["vindexes"], list)
    assert isinstance(snap["cache"], list)


def test_route_plan_generation_matches_shard_map():
    """Route plan generation must mirror the ingested shard map generation."""
    _ingest_base()
    plan = _route_batch(FIX / "batches/mixed-types.json")
    assert plan["generation"] == 1


def test_fresh_routes_use_compute_source():
    """First routing pass must compute shards rather than read warm cache hits."""
    _ingest_base()
    plan = _route_batch(FIX / "batches/mixed-types.json")
    assert plan["cache_hits"] == 0
    assert all(r.get("from") == "compute" for r in plan["routes"])


def test_hash_alice_routes_to_reference_shard():
    """Hash vindex FNV-1a space must resolve alice to the independent reference shard."""
    _ingest_base()
    batch_path = APP / "output/single-hash.json"
    batch_path.write_text(
        json.dumps({"queries": [{"vindex": "user_hash", "key": "alice"}]}),
        encoding="utf-8",
    )
    plan = _route_batch(batch_path)
    want = reference_routes(
        FIX / "shardmaps/base-gen1.json",
        FIX / "vindexes/catalog.json",
        batch_path,
    )[0]["shard"]
    assert plan["routes"][0]["shard"] == want


def test_lookup_cust_b_routes_to_reference_shard():
    """Lookup vindex must hash mapped shard names before range resolution."""
    _ingest_base()
    batch_path = APP / "output/single-lookup.json"
    batch_path.write_text(
        json.dumps({"queries": [{"vindex": "customer_lookup", "key": "cust-b"}]}),
        encoding="utf-8",
    )
    plan = _route_batch(batch_path)
    want = reference_routes(
        FIX / "shardmaps/base-gen1.json",
        FIX / "vindexes/catalog.json",
        batch_path,
    )[0]["shard"]
    assert plan["routes"][0]["shard"] == want


def test_binary_long_hex_uses_last_eight_bytes():
    """Binary vindex must keep only the last eight decoded bytes per vindex-contract.md."""
    _ingest_base()
    batch_path = APP / "output/long-binary.json"
    batch_path.write_text(
        json.dumps(
            {"queries": [{"vindex": "order_binary", "key": "0x112233445566778899aabb"}]}
        ),
        encoding="utf-8",
    )
    plan = _route_batch(batch_path)
    want = reference_routes(
        FIX / "shardmaps/base-gen1.json",
        FIX / "vindexes/catalog.json",
        batch_path,
    )[0]["shard"]
    assert plan["routes"][0]["shard"] == want


def test_lookup_missing_param_still_routes_zero_space():
    """Unknown lookup keys use zero routing space and still produce a shard."""
    _ingest_base()
    batch_path = APP / "output/missing-lookup.json"
    batch_path.write_text(
        json.dumps({"queries": [{"vindex": "customer_lookup", "key": "unknown-cust"}]}),
        encoding="utf-8",
    )
    plan = _route_batch(batch_path)
    want = reference_routes(
        FIX / "shardmaps/base-gen1.json",
        FIX / "vindexes/catalog.json",
        batch_path,
    )[0]["shard"]
    assert plan["routes"][0]["shard"] == want


def test_ingest_without_seed_records_zero_coalesce_dropped():
    """Ingest without cache seed must record coalesce_dropped as zero."""
    _ingest_base()
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap.get("coalesce_dropped", 0) == 0


def test_export_audit_includes_snapshot_path():
    """routing-audit.json must echo snapshot_path per export-schema.md."""
    _ingest_base()
    _route_batch(FIX / "batches/mixed-types.json")
    _run(
        [
            CLI,
            "export",
            "--snapshot",
            str(SNAPSHOT),
            "--plan",
            str(PLAN),
            "--audit-out",
            str(AUDIT),
        ]
    )
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert audit["snapshot_path"] == str(SNAPSHOT)


def test_duplicate_keys_in_batch_record_cache_hits():
    """Repeated keys within one route batch must hit cache after the first compute."""
    _ingest_base()
    batch_path = APP / "output/dup-hash.json"
    batch_path.write_text(
        json.dumps(
            {
                "queries": [
                    {"vindex": "user_hash", "key": "alice"},
                    {"vindex": "user_hash", "key": "alice"},
                ]
            }
        ),
        encoding="utf-8",
    )
    plan = _route_batch(batch_path)
    assert plan["cache_hits"] >= 1
    assert plan["routes"][0]["shard"] == plan["routes"][1]["shard"]
