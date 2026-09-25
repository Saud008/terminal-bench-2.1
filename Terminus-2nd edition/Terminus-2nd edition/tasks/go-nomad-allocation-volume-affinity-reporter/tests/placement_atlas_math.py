"""Independent atlas reference math for nomrep — not part of the agent contract."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

SPREAD_WEIGHT = 10


def _scope_alloc(seed: str, alloc_id: str) -> str:
    x = 2166136261
    for b in (seed + ":" + alloc_id).encode():
        x ^= b
        x = (x * 16777619) & 0xFFFFFFFF
    return f"{alloc_id}-{x:08x}"


def _hydrate_allocs(sc: dict[str, Any], seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for a in sc["allocations"]:
        rows.append(
            {
                "alloc_id": _scope_alloc(seed, a["alloc_id"]),
                "job_id": sc["job_id"],
                "task_group": sc["task_group"],
                "node_id": a["node_id"],
                "node_class": a["node_class"],
                "create_index": int(a["create_index"]),
                "modify_index": int(a["modify_index"]),
                "client_status": a["client_status"],
                "desired_status": a["desired_status"],
                "reschedule_attempts": int(a["reschedule_attempts"]),
                "reschedule_failed": bool(a["reschedule_failed"]),
                "csi_mounts": [dict(m) for m in a.get("csi_mounts") or []],
                "constraints": [dict(c) for c in a.get("constraints") or []],
                "affinities": [dict(af) for af in a.get("affinities") or []],
                "superseded_by": a.get("superseded_by") or "",
            }
        )
    return rows


def _node_class_match(c: dict[str, Any], node_class: str) -> bool:
    if c.get("attribute") != "${node.class}":
        return True
    op = c.get("operator")
    val = c.get("value")
    if op == "=":
        return node_class == val
    if op == "!=":
        return node_class != val
    return False


def _affinity_score(af: dict[str, Any], node_pool: str) -> int:
    if af.get("attribute") != "${node.pool}":
        return 0
    op = af.get("operator")
    val = af.get("value")
    weight = int(af.get("weight") or 0)
    if op == "=" and node_pool == val:
        return weight
    if op == "!=" and node_pool != val:
        return weight
    return 0


def _namespace_salt() -> str:
    return os.environ.get("TB3_NAMESPACE_SALT", "")


def _volume_key(vol: dict[str, Any]) -> str:
    key = f"{vol['namespace']}/{vol['volume_id']}"
    salt = _namespace_salt()
    return key + salt if salt else key


def reference_drain_filter(allocs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    eligible: list[dict[str, Any]] = []
    excluded = 0
    for a in allocs:
        if a.get("client_status") == "down" or a.get("desired_status") == "stop":
            excluded += 1
            continue
        eligible.append(a)
    return eligible, excluded


def reference_filter_stale(allocs: list[dict[str, Any]], cutoff: int) -> tuple[list[dict[str, Any]], int]:
    active: list[dict[str, Any]] = []
    suppressed = 0
    for a in allocs:
        if a.get("superseded_by"):
            suppressed += 1
            continue
        if int(a["modify_index"]) < cutoff:
            suppressed += 1
            continue
        active.append(a)
    return active, suppressed


def reference_reschedule_total(allocs: list[dict[str, Any]]) -> int:
    total = 0
    for a in allocs:
        if a.get("reschedule_failed") and int(a["reschedule_attempts"]) > 0:
            total += int(a["reschedule_attempts"])
    return total


def reference_spread_penalty(a: dict[str, Any], peers: list[dict[str, Any]]) -> int:
    count = sum(1 for o in peers if o["node_id"] == a["node_id"] and o["alloc_id"] != a["alloc_id"])
    return count * SPREAD_WEIGHT


def reference_spread_penalty_total(allocs: list[dict[str, Any]]) -> int:
    return sum(reference_spread_penalty(a, allocs) for a in allocs)


def reference_volume_joins(allocs: list[dict[str, Any]], volumes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vol_by_id = {v["volume_id"]: v for v in volumes}
    rows: list[dict[str, Any]] = []
    for a in allocs:
        for m in a.get("csi_mounts") or []:
            vol = vol_by_id.get(m["volume_id"])
            ok = vol is not None
            key = _volume_key(vol) if vol else m["volume_id"]
            rows.append(
                {
                    "alloc_id": a["alloc_id"],
                    "volume_key": key,
                    "plugin_id": vol["plugin_id"] if vol else "",
                    "mount_path": m["mount_path"],
                    "read_only": bool(m.get("read_only")),
                    "join_ok": ok,
                }
            )
    rows.sort(key=lambda r: (r["alloc_id"], r["volume_key"]))
    return rows


def reference_rank_placements(allocs: list[dict[str, Any]], node_pool: str) -> list[dict[str, Any]]:
    passing: list[dict[str, Any]] = []
    for a in allocs:
        hard_ok = all(not c.get("hard") or _node_class_match(c, a["node_class"]) for c in a.get("constraints") or [])
        if not hard_ok:
            continue
        raw = sum(_affinity_score(af, node_pool) for af in a.get("affinities") or [])
        score = raw - reference_spread_penalty(a, allocs)
        passing.append({"alloc": a, "score": score, "hard_ok": hard_ok})
    passing.sort(key=lambda row: (-row["score"], row["alloc"]["alloc_id"]))
    out: list[dict[str, Any]] = []
    for rank, row in enumerate(passing, start=1):
        a = row["alloc"]
        out.append(
            {
                "alloc_id": a["alloc_id"],
                "node_class": a["node_class"],
                "constraint_ok": row["hard_ok"],
                "affinity_score": row["score"],
                "placement_rank": rank,
            }
        )
    return out


def reference_constraint_pass(allocs: list[dict[str, Any]]) -> bool:
    for a in allocs:
        for c in a.get("constraints") or []:
            if c.get("hard") and "${node.class}" in c.get("attribute", "") and not _node_class_match(c, a["node_class"]):
                return False
    return True


def reference_affinity_monotone(placements: list[dict[str, Any]]) -> bool:
    for i in range(1, len(placements)):
        if placements[i]["placement_rank"] < placements[i - 1]["placement_rank"]:
            return False
        if placements[i]["affinity_score"] > placements[i - 1]["affinity_score"]:
            return False
    return True


def reference_audit_digest(summary: dict[str, Any], placements: list[dict[str, Any]], joins: list[dict[str, Any]]) -> str:
    keys = sorted(j["volume_key"] for j in joins)
    ranks = [p["placement_rank"] for p in placements]
    body = (
        "{"
        f'"active_alloc_count":{int(summary["active_alloc_count"])},'
        f'"affinity_monotone_ok":{str(summary["affinity_monotone_ok"]).lower()},'
        f'"constraint_pass_ok":{str(summary["constraint_pass_ok"]).lower()},'
        f'"drain_excluded":{int(summary["drain_excluded"])},'
        f'"placement_ranks":{json.dumps(ranks, separators=(",", ":"))},'
        f'"reschedule_total":{int(summary["reschedule_total"])},'
        f'"spread_penalty_total":{int(summary["spread_penalty_total"])},'
        f'"stale_suppressed":{int(summary["stale_suppressed"])},'
        f'"volume_keys":{json.dumps(keys, separators=(",", ":"))}'
        "}"
    )
    return hashlib.sha256(body.encode()).hexdigest()


def reference_scope_alloc(seed: str, alloc_id: str) -> str:
    """Seed-scoped allocation id (gate-visible reference_* name)."""
    return _scope_alloc(seed, alloc_id)


def reference_load_scenario(path: Path, seed: str) -> dict[str, Any]:
    sc = json.loads(path.read_text(encoding="utf-8"))
    return {
        "scenario_name": sc["scenario_name"],
        "job_id": sc["job_id"],
        "task_group": sc["task_group"],
        "focus_alloc_id": _scope_alloc(seed, sc["focus_alloc_id"]),
        "stale_cutoff_index": int(sc["stale_cutoff_index"]),
        "csi_volumes": sc.get("csi_volumes") or [],
        "allocations": _hydrate_allocs(sc, seed),
    }


def reference_compile_atlas(sc: dict[str, Any], seed: str, *, node_pool: str | None = None) -> dict[str, Any]:
    pool = node_pool if node_pool is not None else os.environ.get("TB3_NODE_POOL", "default")
    drained, drain_excluded = reference_drain_filter(sc["allocations"])
    active, suppressed = reference_filter_stale(drained, int(sc["stale_cutoff_index"]))
    reschedule = reference_reschedule_total(active)
    joins = reference_volume_joins(active, sc["csi_volumes"])
    placements = reference_rank_placements(active, pool)
    summary = {
        "active_alloc_count": len(active),
        "stale_suppressed": suppressed,
        "drain_excluded": drain_excluded,
        "reschedule_total": reschedule,
        "volume_join_count": len(joins),
        "spread_penalty_total": reference_spread_penalty_total(active),
        "constraint_pass_ok": reference_constraint_pass(active),
        "affinity_monotone_ok": reference_affinity_monotone(placements),
    }
    digest = reference_audit_digest(summary, placements, joins)
    return {
        "seed": seed,
        "scenario": sc["scenario_name"],
        "focus_alloc_id": sc["focus_alloc_id"],
        "volume_joins": joins,
        "placements": placements,
        "summary": summary,
        "audit_digest": digest,
    }
