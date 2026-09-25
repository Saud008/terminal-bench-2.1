"""Independent Count-Min Sketch reference for cmsctl verifier."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def seed_offset(seed: str) -> int:
    h = 0xCBF29CE484222325
    for b in seed.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def namespaced_bytes(namespace_salt: str, key: str) -> bytes:
    return namespace_salt.encode("utf-8") + b"\x1f" + key.encode("utf-8")


def row_index(key: str, row: int, seed: int, width: int, namespace_salt: str) -> int:
    data = namespaced_bytes(namespace_salt, key)
    h = seed ^ ((row * 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF)
    for b in data:
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h % width


def build_table(
    width: int,
    depth: int,
    seed: int,
    namespace_salt: str,
    updates: list[tuple[str, int]],
) -> list[list[int]]:
    table = [[0 for _ in range(width)] for _ in range(depth)]
    for key, count in updates:
        for row in range(depth):
            col = row_index(key, row, seed, width, namespace_salt)
            table[row][col] += count
    return table


def estimate(table: list[list[int]], key: str, seed: int, namespace_salt: str) -> int:
    width = len(table[0])
    depth = len(table)
    vals = [table[row][row_index(key, row, seed, width, namespace_salt)] for row in range(depth)]
    return min(vals) if vals else 0


def merge_tables(tables: list[list[list[int]]], weights: list[float]) -> list[list[int]]:
    depth = len(tables[0])
    width = len(tables[0][0])
    out = [[0 for _ in range(width)] for _ in range(depth)]
    for table, weight in zip(tables, weights):
        for row in range(depth):
            for col in range(width):
                scaled = math.floor(table[row][col] * weight)
                out[row][col] = max(out[row][col], scaled)
    return out


def compose_epsilons(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values))


def compute_overlap(shards: list[dict[str, Any]]) -> int:
    start = max(s["window_start_ms"] for s in shards)
    end = min(s["window_end_ms"] for s in shards)
    return max(0, end - start)


def shard_weights(shards: list[dict[str, Any]], overlap_ms: int) -> dict[str, float]:
    out: dict[str, float] = {}
    for shard in shards:
        window_ms = shard["window_end_ms"] - shard["window_start_ms"]
        out[shard["shard_id"]] = 0.0 if window_ms == 0 else overlap_ms / window_ms
    return out


def load_bundle(
    fixture_root: Path,
    seed: str,
    bundle_id: str,
    width_bias: int | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads((fixture_root / "bundles" / f"{bundle_id}.json").read_text(encoding="utf-8"))
    if width_bias is None:
        width_bias = int(__import__("os").environ.get("TB3_WIDTH_BIAS", "0"))
    shards: list[dict[str, Any]] = []
    for ref in manifest["shards"]:
        rel = ref["path"]
        path = fixture_root / rel if not rel.startswith("/") else Path(rel)
        shard = json.loads(path.read_text(encoding="utf-8"))
        shard = dict(shard)
        shard["hash_seed"] = (shard["hash_seed"] + seed_offset(seed)) & 0xFFFFFFFFFFFFFFFF
        if width_bias:
            shard["width"] = max(8, shard["width"] + width_bias)
        shards.append(shard)
    return manifest, shards


def reference_pipeline(
    fixture_root: Path,
    seed: str,
    bundle_id: str,
    width_bias: int | None = None,
) -> dict[str, Any]:
    manifest, shards = load_bundle(fixture_root, seed, bundle_id, width_bias=width_bias)
    overlap_ms = compute_overlap(shards)
    if overlap_ms == 0:
        raise ValueError("zero overlap")
    weights_map = shard_weights(shards, overlap_ms)
    weights = [weights_map[s["shard_id"]] for s in shards]
    tables = []
    for shard in shards:
        updates = [(u["key"], u["count"]) for u in shard["updates"]]
        tables.append(
            build_table(
                shard["width"],
                shard["depth"],
                shard["hash_seed"],
                shard["namespace_salt"],
                updates,
            )
        )
    merged = merge_tables(tables, weights)
    first = shards[0]
    estimates = {
        key: estimate(merged, key, first["hash_seed"], first["namespace_salt"])
        for key in manifest["query_keys"]
    }
    return {
        "bundle_id": bundle_id,
        "overlap_ms": overlap_ms,
        "window_weights": weights_map,
        "epsilon_lineage": {
            "raw_epsilons": [s["epsilon"] for s in shards],
            "composed_epsilon": compose_epsilons([s["epsilon"] for s in shards]),
        },
        "estimates": estimates,
        "hash_seed": first["hash_seed"],
        "width": first["width"],
        "depth": first["depth"],
        "namespace_salt": first["namespace_salt"],
    }
