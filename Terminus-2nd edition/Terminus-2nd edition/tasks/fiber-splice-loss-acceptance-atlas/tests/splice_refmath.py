"""Independent reference math for fsplatlas acceptance atlas."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_samples(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    rows.sort(key=lambda r: (r["distance_m"], r["epoch"]))
    return rows


def scan_reflections(samples: list[dict], threshold_db: float) -> list[dict]:
    events = []
    for prev, cur in zip(samples, samples[1:]):
        delta = prev["power_dbm"] - cur["power_dbm"]
        if delta >= threshold_db:
            events.append(
                {
                    "distance_m": cur["distance_m"],
                    "measured_loss_db": round(delta, 3),
                    "epoch": cur["epoch"],
                }
            )
    return events


def suppress_duplicates(events: list[dict], tolerance_m: float) -> tuple[list[dict], int]:
    buckets: dict[int, dict] = {}
    suppressed = 0
    for ev in events:
        bucket = int(ev["distance_m"] / tolerance_m)
        if bucket in buckets:
            suppressed += 1
            if ev["epoch"] > buckets[bucket]["epoch"]:
                buckets[bucket] = ev
        else:
            buckets[bucket] = ev
    out = sorted(buckets.values(), key=lambda e: e["distance_m"])
    return out, suppressed


def load_inventory(path: Path) -> dict[str, float]:
    data = load_json(path)
    return {row["type"]: row["pair_loss_db"] for row in data["connectors"]}


def bind_segments(
    events: list[dict],
    segments: list[dict],
    splices: list[dict],
    inventory: dict[str, float],
) -> tuple[list[dict], int]:
    planned_by_seg: dict[str, float] = {s["segment_id"]: 0.0 for s in segments}
    for sp in splices:
        for seg in segments:
            if seg["start_m"] <= sp["distance_m"] < seg["end_m"]:
                planned_by_seg[seg["segment_id"]] += sp["planned_loss_db"]
    junction_loss: dict[str, float] = {}
    for i, seg in enumerate(segments):
        if i > 0:
            prev = segments[i - 1]
            key = f"{prev['segment_id']}:{seg['segment_id']}"
            junction_loss[key] = inventory.get(prev["connector_end"], 0.0)
    binds = []
    for seg in segments:
        measured = 0.0
        count = 0
        for ev in events:
            if seg["start_m"] <= ev["distance_m"] < seg["end_m"]:
                measured += ev["measured_loss_db"]
                count += 1
        conn = inventory.get(seg["connector_start"], 0.0)
        if seg["segment_id"] in [s["segment_id"] for s in segments[1:]]:
            pass
        total = round(measured + conn, 3)
        planned = planned_by_seg[seg["segment_id"]]
        binds.append(
            {
                "segment_id": seg["segment_id"],
                "measured_loss_db": round(measured, 3),
                "connector_loss_db": round(conn, 3),
                "total_loss_db": total,
                "accepted": total <= planned + conn + 0.01,
                "bound_event_count": count,
            }
        )
    binds.sort(key=lambda b: b["segment_id"])
    return binds, 0


def audit_digest(atlas: dict) -> str:
    ids = sorted(s["segment_id"] for s in atlas["segments"])
    body = json.dumps(
        {
            "run_id": atlas["run_id"],
            "event_count": atlas["event_count"],
            "accepted_segment_count": atlas["accepted_segment_count"],
            "segment_ids": ids,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def reference_pipeline(root: Path, run_id: str, threshold_override: float | None = None, tol_override: float | None = None) -> dict:
    manifest = load_json(root / "traces" / run_id / "trace_manifest.json")
    threshold = threshold_override if threshold_override is not None else manifest["loss_threshold_db"]
    tol = tol_override if tol_override is not None else manifest["reflection_tolerance_m"]
    samples = load_samples(root / "traces" / run_id / "samples.jsonl")
    events = scan_reflections(samples, threshold)
    events, suppressed = suppress_duplicates(events, tol)
    segments = load_json(root / "routes" / run_id / "segments.json")["segments"]
    splices = load_json(root / "plans" / run_id / "splice_plan.json")["splices"]
    inventory = load_inventory(root / "inventory" / "connectors.json")
    binds, _ = bind_segments(events, segments, splices, inventory)
    accepted = sum(1 for b in binds if b["accepted"])
    atlas = {
        "run_id": run_id,
        "event_count": sum(b["bound_event_count"] for b in binds),
        "accepted_segment_count": accepted,
        "rejected_segment_count": len(binds) - accepted,
        "suppressed_duplicate_count": suppressed,
        "segments": binds,
        "audit_digest": "",
    }
    atlas["audit_digest"] = audit_digest(atlas)
    return atlas
