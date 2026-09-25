"""Independent CRUSH placement trace ledger contract math."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def crush_hash(pool_id: int, pg_num: int, item_id: int, retry: int) -> int:
    payload = f"{pool_id}.{pg_num}.{item_id}.{retry}"
    return int(hashlib.sha256(payload.encode()).hexdigest()[:8], 16)


def effective_weight(osd: dict[str, Any]) -> float:
    return float(osd["weight"]) * float(osd.get("reweight", 1.0))


def osd_eligible(osd: dict[str, Any]) -> bool:
    return osd.get("status") == "up" and bool(osd.get("in", True))


def bucket_by_id(buckets: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(b["id"]): b for b in buckets}


def bucket_by_name(buckets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(b["name"]): b for b in buckets}


def normalize_weights(items: list[tuple[int, float]]) -> list[tuple[int, float]]:
    total = sum(w for _, w in items if w > 0)
    if total <= 0:
        return []
    scale = 65536.0 / total
    return [(i, w * scale) for i, w in items if w > 0]


def weighted_pick(items: list[tuple[int, float]], h: int) -> int:
    total = int(sum(int(w) for _, w in items))
    if not items or total <= 0:
        raise ValueError("empty choice set")
    slot = h % total
    acc = 0
    for item_id, wt in items:
        acc += int(wt)
        if slot < acc:
            return item_id
    return items[-1][0]


def collect_hosts(root: dict[str, Any], buckets: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def walk(bid: int) -> None:
        b = buckets[bid]
        if b["type"] == "host":
            out.append(b)
            return
        for child in b.get("children", []):
            walk(int(child["id"]))

    walk(int(root["id"]))
    out.sort(key=lambda h: str(h["name"]))
    return out


def host_osds(host: dict[str, Any], osds: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for child in host.get("children", []):
        oid = int(child["id"])
        if oid in osds:
            rows.append(osds[oid])
    rows.sort(key=lambda o: int(o["id"]))
    return rows


def choose_acting_set(
    pool: dict[str, Any],
    rule: dict[str, Any],
    buckets: list[dict[str, Any]],
    osds: list[dict[str, Any]],
    pg_num: int,
) -> tuple[list[int], list[dict[str, Any]]]:
    bmap = bucket_by_id(buckets)
    bname = bucket_by_name(buckets)
    omap = {int(o["id"]): o for o in osds}
    steps_out: list[dict[str, Any]] = []
    acting: list[int] = []
    retry = 0
    cursor: dict[str, Any] | None = None
    want = int(pool["size"])

    for step in rule["steps"]:
        op = step["op"]
        if op == "take":
            cursor = bname[str(step["arg"])]
            steps_out.append({"op": "take", "bucket": cursor["name"], "bucket_id": cursor["id"]})
        elif op == "chooseleaf":
            target = int(step["arg"]["num"])
            hosts = collect_hosts(cursor, bmap) if cursor else []
            excluded: set[int] = set()
            for host in hosts:
                for osd in host_osds(host, omap):
                    if not osd_eligible(osd):
                        excluded.add(int(osd["id"]))
            while len(acting) < min(target, want):
                placed = False
                for host in hosts:
                    if len(acting) >= min(target, want):
                        break
                    candidates: list[tuple[int, float]] = []
                    host_excluded: list[int] = []
                    for osd in host_osds(host, omap):
                        oid = int(osd["id"])
                        if not osd_eligible(osd):
                            host_excluded.append(oid)
                            continue
                        if oid in acting:
                            continue
                        candidates.append((oid, effective_weight(osd)))
                    if not candidates:
                        continue
                    norm = normalize_weights(candidates)
                    h = crush_hash(int(pool["id"]), pg_num, int(host["id"]), retry)
                    pick = weighted_pick(norm, h)
                    acting.append(pick)
                    steps_out.append(
                        {
                            "op": "chooseleaf",
                            "host": host["name"],
                            "selected_osd": pick,
                            "excluded_osds": sorted(set(host_excluded) | excluded),
                            "retry": retry,
                        }
                    )
                    retry += 1
                    placed = True
                    break
                if not placed:
                    break
        elif op == "emit":
            steps_out.append({"op": "emit", "acting_set": list(acting)})

    acting = acting[:want]
    return acting, steps_out


def normalized_fingerprint(buckets: list[dict[str, Any]], osds: list[dict[str, Any]]) -> str:
    body = {
        "buckets": [
            {
                "id": b["id"],
                "name": b["name"],
                "type": b["type"],
                "children": b.get("children", []),
            }
            for b in sorted(buckets, key=lambda x: int(x["id"]))
        ],
        "eligible_osds": sorted(
            [
                {"id": o["id"], "eff_weight": effective_weight(o)}
                for o in osds
                if osd_eligible(o)
            ],
            key=lambda r: int(r["id"]),
        ),
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def ledger_digest(run_id: str, pool: dict[str, Any], traces: list[dict[str, Any]]) -> str:
    body = {
        "run_id": run_id,
        "pool_id": pool["id"],
        "pg_traces": [
            {
                "pg_id": t["pg_id"],
                "acting_set": t["acting_set"],
                "primary_osd": t["primary_osd"],
            }
            for t in traces
        ],
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def pg_label(pool_id: int, pg_num: int) -> str:
    return f"{pool_id}.{pg_num:x}"


def reference_ledger(map_dir: Path, run_id: str, pg_start: int, pg_end: int) -> dict[str, Any]:
    buckets = json.loads((map_dir / "crush_map.json").read_text(encoding="utf-8"))["buckets"]
    pool = json.loads((map_dir / "pool.json").read_text(encoding="utf-8"))
    osds = json.loads((map_dir / "osd_map.json").read_text(encoding="utf-8"))["osds"]
    rules = json.loads((map_dir / "crush_map.json").read_text(encoding="utf-8"))["rules"]
    rule = next(r for r in rules if int(r["id"]) == int(pool["crush_rule"]))

    traces: list[dict[str, Any]] = []
    for pg_num in range(pg_start, pg_end + 1):
        acting, steps = choose_acting_set(pool, rule, buckets, osds, pg_num)
        traces.append(
            {
                "pg_id": pg_label(int(pool["id"]), pg_num),
                "pool_id": int(pool["id"]),
                "pg_num": pg_num,
                "primary_osd": acting[0] if acting else -1,
                "acting_set": acting,
                "steps": steps,
            }
        )
    traces.sort(key=lambda t: t["pg_num"])
    fp = normalized_fingerprint(buckets, osds)
    digest = ledger_digest(run_id, pool, traces)
    return {
        "run_id": run_id,
        "map_name": map_dir.name,
        "pool": pool["name"],
        "pool_id": int(pool["id"]),
        "normalized_fingerprint": fp,
        "pg_traces": traces,
        "ledger_digest": digest,
    }
