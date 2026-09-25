"""Independent Lamport refmath for vecchat vcreplay auditor."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

MOD_RANK = {"ban": 4, "kick": 3, "mute": 2, "warn": 1}
DEFAULT_MAX_GAP = 5


def merge_vc(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    out = dict(a)
    for k, vb in b.items():
        va = out.get(k, 0)
        out[k] = max(va, vb)
    return out


def increment_vc(clock: dict[str, int], node: str) -> dict[str, int]:
    out = dict(clock)
    out[node] = out.get(node, 0) + 1
    return out


def happens_before(a: dict[str, int], b: dict[str, int]) -> bool:
    keys = set(a) | set(b)
    strict = False
    for k in keys:
        av = a.get(k, 0)
        bv = b.get(k, 0)
        if av > bv:
            return False
        if av < bv:
            strict = True
    return strict


def concurrent(a: dict[str, int], b: dict[str, int]) -> bool:
    return not happens_before(a, b) and not happens_before(b, a)


def numeric_shard_sort(names: list[str]) -> list[str]:
    def key(n: str) -> int:
        mid = n.removeprefix("shard_").removesuffix(".jsonl")
        return int(mid)

    return sorted(names, key=key)


def load_events(fixture_root: Path, scenario: str) -> list[dict[str, Any]]:
    shard_dir = fixture_root / "rooms" / scenario / "shards"
    names = numeric_shard_sort(
        [p.name for p in shard_dir.glob("shard_*.jsonl") if p.is_file()]
    )
    events: list[dict[str, Any]] = []
    for name in names:
        for line in (shard_dir / name).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def stage_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    staged = []
    for ev in events:
        staged.append(
            {
                "event_id": ev["event_id"],
                "sender": ev["sender"],
                "type": ev["type"],
                "vector_clock": dict(ev["vector_clock"]),
                "timestamp_ms": ev["timestamp_ms"],
                "payload": ev["payload"],
            }
        )
    return staged


def staging_digest(room: str, scenario: str, events: list[dict[str, Any]]) -> str:
    payload = {"room": room, "scenario": scenario, "events": events}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def causal_sort(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    remaining = list(events)
    while remaining:
        ready: list[dict[str, Any]] = []
        for ev in remaining:
            preds = [
                o
                for o in events
                if o["event_id"] != ev["event_id"]
                and happens_before(o["vector_clock"], ev["vector_clock"])
            ]
            if all(p in ordered for p in preds):
                ready.append(ev)
        if not ready:
            ready = [min(remaining, key=lambda e: e["event_id"])]
        pick = min(ready, key=lambda e: e["event_id"])
        ordered.append(pick)
        remaining.remove(pick)
    return ordered


def max_gap() -> int:
    bias = 0
    raw = os.environ.get("TB3_GAP_BIAS", "")
    if raw:
        try:
            bias = int(raw)
        except ValueError:
            bias = 0
    return DEFAULT_MAX_GAP + bias


def reference_findings(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    by_id = {ev["event_id"]: ev for ev in events}
    sorted_ev = causal_sort(events)
    frontier: dict[str, int] = {}
    for ev in sorted_ev:
        expected = increment_vc(dict(frontier), ev["sender"])
        if expected != ev["vector_clock"]:
            findings.append(
                {"code": "clock_drift", "event_id": ev["event_id"], "detail": "frontier_mismatch"}
            )
        frontier = merge_vc(frontier, ev["vector_clock"])

    mods = [ev for ev in sorted_ev if ev["type"] == "moderation"]
    for i, a in enumerate(mods):
        for b in mods[i + 1 :]:
            ta, tb = a["payload"]["target"], b["payload"]["target"]
            if ta != tb:
                continue
            if concurrent(a["vector_clock"], b["vector_clock"]):
                ra, rb = MOD_RANK[a["payload"]["action"]], MOD_RANK[b["payload"]["action"]]
                if ra > rb:
                    findings.append(
                        {
                            "code": "moderation_conflict",
                            "event_id": b["event_id"],
                            "detail": "lower_rank_suppressed",
                        }
                    )
                elif rb > ra:
                    findings.append(
                        {
                            "code": "moderation_conflict",
                            "event_id": a["event_id"],
                            "detail": "lower_rank_suppressed",
                        }
                    )

    mutes = [
        ev["payload"]
        for ev in sorted_ev
        if ev["type"] == "mute_start"
    ]
    for ev in sorted_ev:
        if ev["type"] != "message":
            continue
        for mw in mutes:
            if ev["sender"] == mw["target"] and mw["start_ms"] <= ev["timestamp_ms"] < mw["end_ms"]:
                findings.append(
                    {"code": "mute_leak", "event_id": ev["event_id"], "detail": "active_mute"}
                )

    receipts = [ev for ev in sorted_ev if ev["type"] == "receipt"]
    for rec in receipts:
        rp = rec["payload"]
        ref = by_id.get(rp["ref_event_id"])
        if not ref or not receipt_valid(ref["vector_clock"], rp["delivered_clock"]):
            findings.append(
                {"code": "receipt_mismatch", "event_id": rec["event_id"], "detail": "invalid_delivery"}
            )

    for i, a in enumerate(receipts):
        for b in receipts[i + 1 :]:
            ra, rb = a["payload"], b["payload"]
            if ra["ref_event_id"] == rb["ref_event_id"] and ra["recipient"] == rb["recipient"]:
                loser = b if b["event_id"] > a["event_id"] else a
                findings.append(
                    {
                        "code": "duplicate_delivery",
                        "event_id": loser["event_id"],
                        "detail": "suppressed",
                    }
                )

    mg = max_gap()
    for i in range(1, len(sorted_ev)):
        prev, nxt = sorted_ev[i - 1]["vector_clock"], sorted_ev[i]["vector_clock"]
        keys = set(prev) | set(nxt)
        for k in keys:
            if abs(nxt.get(k, 0) - prev.get(k, 0)) > mg:
                findings.append(
                    {"code": "clock_gap", "event_id": sorted_ev[i]["event_id"], "detail": "adjacent_gap"}
                )
                break

    findings.sort(key=lambda f: (f["event_id"], f["code"]))
    return findings


def receipt_valid(ref_clock: dict[str, int], delivered: dict[str, int]) -> bool:
    return happens_before(delivered, ref_clock) or delivered == ref_clock


def suppressed_receipts(events: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    receipts = [ev for ev in events if ev["type"] == "receipt"]
    for i, a in enumerate(receipts):
        for b in receipts[i + 1 :]:
            ra, rb = a["payload"], b["payload"]
            if ra["ref_event_id"] == rb["ref_event_id"] and ra["recipient"] == rb["recipient"]:
                loser = b if b["event_id"] > a["event_id"] else a
                out.add(loser["event_id"])
    return out


def effective_moderation(events: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for ev in causal_sort(events):
        if ev["type"] != "moderation":
            continue
        mp = ev["payload"]
        cur = out.get(mp["target"])
        if cur is None or MOD_RANK[mp["action"]] > MOD_RANK[cur]:
            out[mp["target"]] = mp["action"]
    return out


def reference_timeline_rows(room: str, scenario: str, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_ev = causal_sort(events)
    suppressed = suppressed_receipts(sorted_ev)
    eff = effective_moderation(sorted_ev)
    mutes = [ev["payload"] for ev in sorted_ev if ev["type"] == "mute_start"]
    rows: list[dict[str, Any]] = []
    seq = 0
    for ev in sorted_ev:
        if ev["type"] == "receipt" and ev["event_id"] in suppressed:
            continue
        seq += 1
        visible = True
        if ev["type"] == "message":
            mod = eff.get(ev["sender"])
            if mod in ("ban", "kick"):
                visible = False
            for mw in mutes:
                if ev["sender"] == mw["target"] and mw["start_ms"] <= ev["timestamp_ms"] < mw["end_ms"]:
                    visible = False
        rows.append(
            {
                "seq": seq,
                "event_id": ev["event_id"],
                "type": ev["type"],
                "sender": ev["sender"],
                "vector_clock": ev["vector_clock"],
                "visible": visible,
            }
        )
    digest = timeline_digest(room, scenario, rows)
    if rows:
        rows[-1] = {**rows[-1], "timeline_digest": digest}
    return rows


def timeline_digest(room: str, scenario: str, rows: list[dict[str, Any]]) -> str:
    plain = [
        {
            "seq": r["seq"],
            "event_id": r["event_id"],
            "type": r["type"],
            "sender": r["sender"],
            "vector_clock": r["vector_clock"],
            "visible": r["visible"],
        }
        for r in rows
    ]
    payload = {"room": room, "scenario": scenario, "rows": plain}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def reference_staging(room: str, scenario: str, fixture_root: Path) -> dict[str, Any]:
    events = stage_events(load_events(fixture_root, scenario))
    return {
        "engine": "vcreplay-v1",
        "room": room,
        "scenario": scenario,
        "shard_count": len(list((fixture_root / "rooms" / scenario / "shards").glob("shard_*.jsonl"))),
        "event_count": len(events),
        "events": events,
        "staging_digest": staging_digest(room, scenario, events),
    }


def reference_findings_report(scenario: str, fixture_root: Path) -> dict[str, Any]:
    events = stage_events(load_events(fixture_root, scenario))
    findings = reference_findings(events)
    return {
        "scenario": scenario,
        "finding_count": len(findings),
        "findings": findings,
    }
