"""Independent wildfire evacuation verifier math."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def point_in_polygon(pt: tuple[float, float], poly: list[dict[str, float]]) -> bool:
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]["x"], poly[i]["y"]
        x2, y2 = poly[(i + 1) % n]["x"], poly[(i + 1) % n]["y"]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1):
            inside = not inside
    return inside


def segments_intersect(a1, a2, b1, b2) -> bool:
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_seg(p, q, r):
        return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])

    o1 = orient(a1, a2, b1)
    o2 = orient(a1, a2, b2)
    o3 = orient(b1, b2, a1)
    o4 = orient(b1, b2, a2)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    if o1 == 0 and on_seg(a1, b1, a2):
        return True
    if o2 == 0 and on_seg(a1, b2, a2):
        return True
    if o3 == 0 and on_seg(b1, a1, b2):
        return True
    return bool(o4 == 0 and on_seg(b1, a2, b2))


def polygons_intersect(a: list[dict[str, float]], b: list[dict[str, float]]) -> bool:
    for poly, other in ((a, b), (b, a)):
        for p in poly:
            if point_in_polygon((p["x"], p["y"]), other):
                return True
        for i in range(len(poly)):
            a1 = (poly[i]["x"], poly[i]["y"])
            a2 = (poly[(i + 1) % len(poly)]["x"], poly[(i + 1) % len(poly)]["y"])
            for j in range(len(other)):
                b1 = (other[j]["x"], other[j]["y"])
                b2 = (other[(j + 1) % len(other)]["x"], other[(j + 1) % len(other)]["y"])
                if segments_intersect(a1, a2, b1, b2):
                    return True
    return False


def overlap_ratio(zone: list[dict[str, float]], fire: list[dict[str, float]]) -> float:
    if not polygons_intersect(zone, fire):
        return 0.0
    xs = [p["x"] for p in zone]
    ys = [p["y"] for p in zone]
    area = (max(xs) - min(xs)) * (max(ys) - min(ys))
    if area <= 0:
        return 0.0
    fx = [p["x"] for p in fire]
    fy = [p["y"] for p in fire]
    ix = max(0.0, min(max(xs), max(fx)) - max(min(xs), min(fx)))
    iy = max(0.0, min(max(ys), max(fy)) - max(min(ys), min(fy)))
    return min(1.0, (ix * iy) / area)


def centroid(poly: list[dict[str, float]]) -> tuple[float, float]:
    n = max(len(poly), 1)
    sx = sum(p["x"] for p in poly)
    sy = sum(p["y"] for p in poly)
    return sx / n, sy / n


def nearest_node(roads: dict[str, Any], pt: tuple[float, float]) -> str:
    best = None
    best_d = float("inf")
    for node in roads["nodes"]:
        d = (node["x"] - pt[0]) ** 2 + (node["y"] - pt[1]) ** 2
        if d < best_d:
            best_d = d
            best = node["id"]
    assert best is not None
    return best


def shortest_path_km(roads: dict[str, Any], start: tuple[float, float], goal: tuple[float, float]) -> float | None:
    start_id = nearest_node(roads, start)
    goal_id = nearest_node(roads, goal)
    if start_id == goal_id:
        return 0.0
    adj: dict[str, list[tuple[str, float]]] = {}
    for edge in roads["edges"]:
        if edge.get("closed"):
            continue
        adj.setdefault(edge["from"], []).append((edge["to"], edge["km"]))
        adj.setdefault(edge["to"], []).append((edge["from"], edge["km"]))
    dist = {start_id: 0.0}
    frontier = [start_id]
    while frontier:
        cur = frontier.pop(0)
        base = dist[cur]
        for nxt, km in adj.get(cur, []):
            nd = base + km
            if nxt not in dist or nd < dist[nxt]:
                dist[nxt] = nd
                frontier.append(nxt)
    return dist.get(goal_id)


def classify_severity(ratio: float, policy: dict[str, Any]) -> str:
    if ratio >= policy["immediate_overlap"]:
        return "IMMEDIATE"
    if ratio >= policy["urgent_overlap"]:
        return "URGENT"
    if ratio > 0.0:
        return "ADVISORY"
    return "NONE"


def weave_reference(bundle: dict[str, Any], run_id: str) -> dict[str, Any]:
    remaining = {s["shelter_id"]: s["capacity"] for s in bundle["shelters"]}
    assignments: list[dict[str, Any]] = []
    zone_alerts: list[dict[str, Any]] = []
    zones = sorted(bundle["zones"], key=lambda z: z["zone_id"])
    for zone in zones:
        best_ratio = 0.0
        for fire in bundle["fires"]:
            best_ratio = max(best_ratio, overlap_ratio(zone["polygon"], fire["perimeter"]))
        severity = classify_severity(best_ratio, bundle["policy"])
        if severity == "NONE":
            continue
        cx, cy = centroid(zone["polygon"])
        best: tuple[str, float] | None = None
        for shelter in bundle["shelters"]:
            km = shortest_path_km(bundle["roads"], (cx, cy), (shelter["location"]["x"], shelter["location"]["y"]))
            if km is None:
                continue
            if best is None or km < best[1] or (km == best[1] and shelter["shelter_id"] < best[0]):
                best = (shelter["shelter_id"], km)
        if best is None:
            continue
        sid, routed_km = best
        need = zone["population"]
        if remaining.get(sid, 0) < need:
            continue
        remaining[sid] -= need
        message = bundle["templates"].get(zone["zone_id"], f"Evacuate zone {zone['zone_id']}")
        assignments.append({"zone_id": zone["zone_id"], "shelter_id": sid, "routed_km": routed_km, "evacuees": need})
        zone_alerts.append({"zone_id": zone["zone_id"], "severity": severity, "shelter_id": sid, "message": message, "overlap_ratio": best_ratio})
    body = {"assignments": assignments, "run_id": run_id, "scenario": bundle["scenario"], "zone_alerts": zone_alerts}
    weave_digest = hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest()
    return {"run_id": run_id, "scenario": bundle["scenario"], "assignments": assignments, "zone_alerts": zone_alerts, "policy": bundle["policy"], "weave_digest": weave_digest}


def seal_reference(staging: dict[str, Any]) -> dict[str, Any]:
    # Prefer policy ranks from the ledger when present (lower = more urgent).
    policy_ranks = dict(staging.get("policy", {}).get("severity_ranks") or {})
    if not policy_ranks:
        policy_ranks = {"IMMEDIATE": 0, "URGENT": 1, "ADVISORY": 2, "NONE": 99}
    bundles = []
    for z in staging["zone_alerts"]:
        routed = next(a["routed_km"] for a in staging["assignments"] if a["zone_id"] == z["zone_id"])
        bundles.append({"zone_id": z["zone_id"], "severity": z["severity"], "shelter_id": z["shelter_id"], "message": z["message"], "overlap_ratio": z["overlap_ratio"], "routed_km": routed})
    bundles.sort(key=lambda b: (policy_ranks.get(b["severity"], 99), b["zone_id"]))
    summary = {"bundle_count": len(bundles), "total_evacuees": sum(a["evacuees"] for a in staging["assignments"])}
    bundle_digest = hashlib.sha256(json.dumps({"bundles": bundles}, separators=(",", ":")).encode()).hexdigest()
    return {"run_id": staging["run_id"], "weave_digest": staging["weave_digest"], "bundles": bundles, "summary": summary, "bundle_digest": bundle_digest}


def load_scenario(scenario_dir: Path) -> dict[str, Any]:
    return {
        "scenario": scenario_dir.name,
        "zones": json.loads((scenario_dir / "zones.json").read_text(encoding="utf-8")),
        "fires": json.loads((scenario_dir / "fires.json").read_text(encoding="utf-8")),
        "shelters": json.loads((scenario_dir / "shelters.json").read_text(encoding="utf-8")),
        "roads": json.loads((scenario_dir / "roads.json").read_text(encoding="utf-8")),
        "templates": json.loads((scenario_dir / "templates.json").read_text(encoding="utf-8")),
        "policy": json.loads((scenario_dir / "policy.json").read_text(encoding="utf-8")),
    }


def reference_seal_bundle(scenario_dir: Path, run_id: str) -> dict[str, Any]:
    ledger = weave_reference(load_scenario(scenario_dir), run_id)
    return seal_reference(ledger)
