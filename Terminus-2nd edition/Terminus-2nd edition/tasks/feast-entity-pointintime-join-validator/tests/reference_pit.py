"""Independent reference for feastctl point-in-time join validator."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def scoped_id(seed: str, base: str) -> str:
    x = 2166136261
    for b in (seed + ":" + base).encode():
        x ^= b
        x = (x * 16777619) & 0xFFFFFFFF
    return f"{base}-{x:08x}"


def materialize(sc: dict[str, Any], seed: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ev in sc["events"]:
        row = {
            "entity_id": scoped_id(seed, ev["entity_base"]),
            "event_ts": ev["event_ts"],
            "feature": ev["feature"],
            "value": ev["value"],
            "source": ev["source"],
            "partition": ev["partition"],
            "seq": ev["seq"],
        }
        if ev.get("device_base"):
            row["device_id"] = scoped_id(seed, ev["device_base"])
        if ev.get("session_base"):
            row["session_id"] = scoped_id(seed, ev["session_base"])
        out.append(row)
    return out


def dedupe(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    best: dict[tuple, dict[str, Any]] = {}
    for ev in events:
        k = (
            ev["entity_id"],
            ev.get("device_id", ""),
            ev.get("session_id", ""),
            ev["feature"],
            ev["source"],
            ev["event_ts"],
        )
        if k not in best or ev["seq"] > best[k]["seq"]:
            best[k] = ev
    out = sorted(best.values(), key=lambda e: (e["event_ts"], e["entity_id"]))
    return out, len(events) - len(out)


def within_window(event_ts: int, as_of: int, ttl: int) -> bool:
    return event_ts <= as_of and (as_of - event_ts) <= ttl


def partition_ok(part: str, active: str) -> bool:
    return part == active


def entity_match(keys: list[str], ev: dict[str, Any], entity_id: str, device_id: str, session_id: str) -> bool:
    if not keys or ev["entity_id"] != entity_id:
        return False
    if len(keys) == 1:
        return True
    if keys[1] == "device_id":
        return ev.get("device_id") == device_id
    if keys[1] == "session_id":
        return ev.get("session_id") == session_id
    return False


def select_pit(events: list[dict], keys: list[str], entity_id: str, device_id: str, session_id: str, feature: str, source: str, as_of: int) -> dict | None:
    best = None
    for ev in events:
        if ev["feature"] != feature or ev["source"] != source:
            continue
        if not entity_match(keys, ev, entity_id, device_id, session_id):
            continue
        if ev["event_ts"] > as_of:
            continue
        if best is None or ev["event_ts"] > best["event_ts"]:
            best = ev
    return best


def round3(v: float) -> float:
    # Half-away-from-zero for non-negative values (matches Go int64(v*1000+0.5)/1000).
    if v >= 0:
        return int(v * 1000 + 0.5) / 1000.0
    return -int((-v) * 1000 + 0.5) / 1000.0


def values_match(a: float, b: float) -> bool:
    return round3(a) == round3(b)


def canonical_summary(summary: dict[str, Any]) -> str:
    as_of = summary["as_of_ts"]
    parts = [
        '"as_of_ts":[' + ",".join(str(int(x)) for x in as_of) + "]",
        f'"duplicate_ts_resolved":{int(summary["duplicate_ts_resolved"])}',
        f'"mismatch_count":{int(summary["mismatch_count"])}',
        f'"ttl_filtered_count":{int(summary["ttl_filtered_count"])}',
    ]
    return "{" + ",".join(parts) + "}"


def audit_digest(summary: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_summary(summary).encode()).hexdigest()


def load_scenario(path: Path, seed: str) -> dict[str, Any]:
    sc = json.loads(path.read_text(encoding="utf-8"))
    sc["_materialized"] = materialize(sc, seed)
    return sc


def reference_validate(sc: dict[str, Any], ttl_seconds: int) -> dict[str, Any]:
    deduped, dup_resolved = dedupe(sc["_materialized"])
    ttl_filtered = 0
    rows: list[dict[str, Any]] = []
    mismatch = 0
    as_of_list: list[int] = []

    for entry in sc["as_of_entries"]:
        as_of = entry["as_of_ts"]
        active = entry["active_partition"]
        as_of_list.append(as_of)
        filtered = []
        for ev in deduped:
            if not within_window(ev["event_ts"], as_of, ttl_seconds):
                ttl_filtered += 1
                continue
            if not partition_ok(ev["partition"], active):
                continue
            filtered.append(ev)
        targets: dict[tuple, dict] = {}
        for ev in filtered:
            k = (ev["entity_id"], ev.get("device_id", ""), ev.get("session_id", ""), ev["feature"])
            targets[k] = ev
        for (_e, device_id, session_id, feature), _ in sorted(targets.items(), key=lambda x: (x[0][0], x[0][3])):
            entity_id = _e
            off = select_pit(filtered, sc["entity_keys"], entity_id, device_id, session_id, feature, "offline", as_of)
            on = select_pit(filtered, sc["entity_keys"], entity_id, device_id, session_id, feature, "online", as_of)
            row = {"entity_id": entity_id, "feature": feature, "as_of_ts": as_of, "match_ok": True, "reason": "ok"}
            if off:
                row["offline_value"] = off["value"]
            if on:
                row["online_value"] = on["value"]
            if off is None or on is None:
                row["match_ok"] = False
                row["reason"] = "missing_side"
                mismatch += 1
            elif not values_match(off["value"], on["value"]):
                row["match_ok"] = False
                row["reason"] = "value_mismatch"
                mismatch += 1
            rows.append(row)

    as_of_list = sorted(as_of_list)
    summary = {
        "mismatch_count": mismatch,
        "ttl_filtered_count": ttl_filtered,
        "duplicate_ts_resolved": dup_resolved,
        "as_of_ts": as_of_list,
    }
    return {
        "parity_ok": mismatch == 0,
        "summary": summary,
        "rows": rows,
        "audit_digest": audit_digest(summary),
    }


def reference_report(seed: str, scenario: str, run_id: int, ref: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": seed,
        "scenario": scenario,
        "run_id": run_id,
        "parity_ok": ref["parity_ok"],
        "summary": ref["summary"],
        "audit_digest": ref["audit_digest"],
    }


def tb3_ttl_bias() -> int:
    raw = os.environ.get("TB3_TTL_BIAS", "0")
    try:
        return int(raw)
    except ValueError:
        return 0
