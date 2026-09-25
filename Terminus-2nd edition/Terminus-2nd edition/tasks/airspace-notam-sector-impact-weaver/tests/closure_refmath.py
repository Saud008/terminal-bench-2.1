"""Independent reference math for airclos impact-closure atlases."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


def eval_minute(policy: dict) -> int:
    raw = os.environ.get("LAB_EVAL_MINUTE")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return int(policy["eval_minute"])


# Go struct field order (encoding/json) — do not alphabetize nested objects.
_NOTAM_KEYS = (
    "notam_id",
    "series_id",
    "amendment",
    "start_minute",
    "end_minute",
    "kind",
    "sector_id",
    "polygon",
    "airport",
    "runway",
    "route_fix",
    "airway_id",
    "impact_code",
)
_SECTOR_KEYS = ("sector_id", "polygon")
_FLIGHT_KEYS = ("flight_id", "route_fixes", "runways", "airport")
_AIRWAY_KEYS = ("airway_id", "fixes")
_FIX_KEYS = ("fix_id", "x", "y")
_POINT_KEYS = ("x", "y")
_POLICY_KEYS = ("eval_minute",)
_OMIT_EMPTY = frozenset(
    {"sector_id", "polygon", "airport", "runway", "route_fix", "airway_id", "runways"}
)


def _ordered(obj: dict, keys: tuple[str, ...]) -> dict:
    out = {}
    for k in keys:
        if k not in obj:
            continue
        v = obj[k]
        if k in _OMIT_EMPTY and (v is None or v == "" or v == [] or v == {}):
            continue
        if k == "polygon" and isinstance(v, list):
            out[k] = [_ordered(p, _POINT_KEYS) if isinstance(p, dict) else p for p in v]
        else:
            out[k] = v
    return out


def _dumps_go_map(payload: dict) -> bytes:
    """Match Go json.Marshal(map[string]any): sort map keys; nested structs keep field order."""
    items = []
    for k in sorted(payload):
        items.append(
            json.dumps(k, separators=(",", ":"))
            + ":"
            + json.dumps(payload[k], separators=(",", ":"))
        )
    return ("{" + ",".join(items) + "}").encode()


def load_scenario(scenario: str, fixture_root: Path) -> dict:
    base = fixture_root / "scenarios" / scenario
    notams = []
    for line in (base / "notams.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            notams.append(json.loads(line))
    sectors = json.loads((base / "sectors.json").read_text(encoding="utf-8"))
    flights = []
    for line in (base / "flights.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            flights.append(json.loads(line))
    fix_points = json.loads((base / "fix_points.json").read_text(encoding="utf-8"))
    airways = json.loads((base / "airways.json").read_text(encoding="utf-8"))
    policy = json.loads((base / "policy.json").read_text(encoding="utf-8"))
    return {
        "notams": notams,
        "sectors": sectors,
        "flights": flights,
        "fix_points": fix_points,
        "airways": airways,
        "policy": policy,
    }


def reference_binding_digest(scenario: str, fixture_root: Path) -> str:
    data = load_scenario(scenario, fixture_root)
    payload = {
        "policy": _ordered(data["policy"], _POLICY_KEYS),
        "scenario": scenario,
        "notams": [_ordered(n, _NOTAM_KEYS) for n in data["notams"]],
        "sectors": [_ordered(s, _SECTOR_KEYS) for s in data["sectors"]],
        "flights": [_ordered(f, _FLIGHT_KEYS) for f in data["flights"]],
        "airways": [_ordered(a, _AIRWAY_KEYS) for a in data["airways"]],
        "fix_points": [_ordered(fp, _FIX_KEYS) for fp in data["fix_points"]],
    }
    raw = _dumps_go_map(payload)
    return hashlib.sha256(raw).hexdigest()


def close_amendments(notams: list[dict]) -> list[dict]:
    best: dict[str, dict] = {}
    for row in notams:
        sid = row["series_id"]
        cur = best.get(sid)
        if cur is None or row["amendment"] > cur["amendment"]:
            best[sid] = row
    out = list(best.values())
    out.sort(key=lambda r: r["notam_id"])
    return out


# Backward-friendly alias used by the lemma unit module.
suppress_amendments = close_amendments


def active_at(start_min: int, end_min: int, eval_min: int) -> bool:
    if end_min >= start_min:
        return start_min <= eval_min <= end_min
    return eval_min >= start_min or eval_min <= end_min


def normalize_runway(raw: str) -> str:
    s = raw.strip().upper()
    m = re.match(r"^0*(\d+)([LRC]?)$", s)
    if not m:
        return s
    num, suffix = m.group(1), m.group(2)
    return f"{num}{suffix}"


def airway_map(airways: list[dict]) -> dict[str, list[str]]:
    return {a["airway_id"]: list(a["fixes"]) for a in airways}


def expand_route(fixes: list[str], catalog: dict[str, list[str]]) -> list[str]:
    out: list[str] = []
    for token in fixes:
        if token in catalog:
            seq = list(catalog[token])
            if out and seq and out[-1] == seq[0]:
                seq = seq[1:]
            out.extend(seq)
        else:
            if out and out[-1] == token:
                continue
            out.append(token)
    return out


def point_on_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> bool:
    cross = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
    if abs(cross) > 1e-9:
        return False
    dot = (px - x1) * (px - x2) + (py - y1) * (py - y2)
    return dot <= 1e-9


def point_in_polygon(px: float, py: float, poly: list[dict]) -> bool:
    n = len(poly)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]["x"], poly[i]["y"]
        xj, yj = poly[j]["x"], poly[j]["y"]
        if point_on_segment(px, py, xi, yi, xj, yj):
            return True
        intersect = (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 0.0) + xi
        if intersect:
            inside = not inside
        j = i
    return inside


def fix_coord_map(fix_points: list[dict]) -> dict[str, tuple[float, float]]:
    return {f["fix_id"]: (f["x"], f["y"]) for f in fix_points}


def resolve_active_chronology(scenario: str, fixture_root: Path) -> tuple[list[dict], int]:
    data = load_scenario(scenario, fixture_root)
    em = eval_minute(data["policy"])
    closed = close_amendments(data["notams"])
    active = [n for n in closed if active_at(n["start_minute"], n["end_minute"], em)]
    return active, em


def reference_closure_lattice(scenario: str, fixture_root: Path) -> dict:
    data = load_scenario(scenario, fixture_root)
    active, em = resolve_active_chronology(scenario, fixture_root)
    catalog = airway_map(data["airways"])
    coords = fix_coord_map(data["fix_points"])
    sector_set: set[str] = set()
    closures: list[dict] = []

    for flight in data["flights"]:
        expanded = expand_route(flight["route_fixes"], catalog)
        for fix in expanded:
            if fix in coords:
                x, y = coords[fix]
                for sec in data["sectors"]:
                    if point_in_polygon(x, y, sec["polygon"]):
                        sector_set.add(sec["sector_id"])
        for notam in active:
            kind = notam["kind"]
            if kind == "sector":
                poly = notam["polygon"]
                for fix in expanded:
                    if fix in coords:
                        x, y = coords[fix]
                        if point_in_polygon(x, y, poly):
                            sector_set.add(notam["sector_id"])
                            closures.append(
                                {
                                    "flight_id": flight["flight_id"],
                                    "impact_code": "sector_penetration",
                                    "detail": notam["sector_id"],
                                    "notam_id": notam["notam_id"],
                                }
                            )
            elif kind == "runway":
                ap = flight.get("airport", "").strip().upper()
                n_ap = notam.get("airport", "").strip().upper()
                for rw in flight.get("runways", []):
                    if ap == n_ap and normalize_runway(rw) == normalize_runway(notam["runway"]):
                        closures.append(
                            {
                                "flight_id": flight["flight_id"],
                                "impact_code": "runway_closure",
                                "detail": notam["runway"],
                                "notam_id": notam["notam_id"],
                            }
                        )
            elif kind == "route":
                target = notam.get("route_fix") or notam.get("airway_id", "")
                for fix in expanded:
                    if fix == target:
                        closures.append(
                            {
                                "flight_id": flight["flight_id"],
                                "impact_code": "route_restriction",
                                "detail": target,
                                "notam_id": notam["notam_id"],
                            }
                        )
    closures.sort(key=lambda r: (r["flight_id"], r["notam_id"]))
    sectors = sorted(sector_set)
    return {
        "scenario": scenario,
        "eval_minute": em,
        "sealed_sectors": sectors,
        "route_closures": closures,
        "active_notam_count": len(active),
    }


def reference_impact_atlas(scenario: str, fixture_root: Path) -> dict:
    lattice = reference_closure_lattice(scenario, fixture_root)
    atlas = {
        "scenario": scenario,
        "eval_minute": lattice["eval_minute"],
        "active_notam_count": lattice["active_notam_count"],
        "sealed_sectors": lattice["sealed_sectors"],
        "route_closures": lattice["route_closures"],
    }
    payload = {
        "active_notam_count": atlas["active_notam_count"],
        "sealed_sectors": atlas["sealed_sectors"],
        "eval_minute": atlas["eval_minute"],
        "route_closures": atlas["route_closures"],
        "scenario": atlas["scenario"],
    }
    raw = _dumps_go_map(payload)
    atlas["atlas_digest"] = hashlib.sha256(raw).hexdigest()
    return atlas
