"""Independent geo filter playfield puzzle authority."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

PRIORITY = [
    "blocked_pin",
    "blocked_bbox",
    "blocked_replica_lag",
    "blocked_doc_floor",
    "blocked_admit_cap",
]


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def apply_pin_salt(inv: dict[str, Any], salt: str) -> dict[str, Any]:
    out = json.loads(json.dumps(inv))
    if salt:
        for doc in out.get("documents", []):
            pins = doc.get("filter_pins") or []
            doc["filter_pins"] = [p + salt for p in pins]
    return out


def reference_evaluate(inv: dict[str, Any]) -> dict[str, Any]:
    lag_ok = int(inv["lag_ms"]) < int(inv["lag_ceiling_ms"])
    win = inv["window"]
    focus = inv["focus"]
    max_admit = int(inv["max_admit"])
    doc_floor = int(inv["doc_floor"])
    pin_blocked: dict[str, str] = {}
    bbox_blocked: dict[str, str] = {}
    for doc in inv.get("documents", []):
        if doc.get("kind") != "document":
            continue
        did = doc["doc_id"]
        if doc.get("filter_pins"):
            pin_blocked[did] = "blocked_pin"
        lon, lat = float(doc["lon"]), float(doc["lat"])
        inside = (
            float(win["min_lon"]) <= lon <= float(win["max_lon"])
            and float(win["min_lat"]) <= lat <= float(win["max_lat"])
        )
        if not inside:
            bbox_blocked[did] = "blocked_bbox"
    denied: dict[str, str] = {}
    candidates: list[dict[str, Any]] = []
    for doc in inv.get("documents", []):
        if doc.get("kind") != "document":
            continue
        did = doc["doc_id"]
        reasons: list[str] = []
        if did in pin_blocked:
            reasons.append("blocked_pin")
        if did in bbox_blocked:
            reasons.append("blocked_bbox")
        if not lag_ok:
            reasons.append("blocked_replica_lag")
        if reasons:
            reasons.sort(key=lambda r: PRIORITY.index(r))
            denied[did] = reasons[0]
        else:
            aff = 1.0 / (
                1.0
                + haversine_km(
                    float(focus["lon"]),
                    float(focus["lat"]),
                    float(doc["lon"]),
                    float(doc["lat"]),
                )
            )
            candidates.append(
                {
                    "doc_id": did,
                    "lon": float(doc["lon"]),
                    "lat": float(doc["lat"]),
                    "affinity": aff,
                }
            )
    if len(candidates) < doc_floor:
        for row in candidates:
            denied[row["doc_id"]] = "blocked_doc_floor"
        candidates = []
    candidates.sort(key=lambda r: (-float(r["affinity"]), r["doc_id"]))
    ranked = [{**row, "admit_rank": i} for i, row in enumerate(candidates, 1)]
    admitted = ranked[:max_admit]
    for row in ranked[max_admit:]:
        denied[row["doc_id"]] = "blocked_admit_cap"
    return {
        "admitted": admitted,
        "denied": [
            {"doc_id": n, "deny_reason": r} for n, r in sorted(denied.items())
        ],
        "admitted_count": len(admitted),
        "denied_count": len(denied),
    }


evaluate = reference_evaluate


def reference_atlas_digest(
    admitted: list[dict[str, Any]], digits: int | None = None
) -> str:
    if digits is None:
        digits = int(os.environ.get("TB3_PLAY_DIGITS") or "4")
    rows = sorted(admitted, key=lambda r: int(r["admit_rank"]))
    payload = "".join(
        f"{r['doc_id']}:{float(r['affinity']):.{digits}f}" + chr(10) for r in rows
    )
    return hashlib.sha256(payload.encode()).hexdigest()


atlas_digest = reference_atlas_digest
audit_digest = reference_atlas_digest


def load_level(path: Path, salt: str = "") -> dict[str, Any]:
    inv = json.loads(path.read_text(encoding="utf-8"))
    return apply_pin_salt(inv, salt)
