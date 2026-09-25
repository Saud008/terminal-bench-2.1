"""Independent GeoJSON ring repair reference per /app/docs/."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

STAT_KEYS = (
    "fixtures_read",
    "exterior_reversed",
    "interior_reversed",
    "duplicate_vertices_removed",
    "closing_vertices_normalized",
    "rings_reordered",
    "multipolygon_members",
)


def floatify_coordinates(obj: Any) -> Any:
    if isinstance(obj, list):
        if obj and isinstance(obj[0], (int, float)) and not isinstance(obj[0], (list, dict)):
            return [float(value) for value in obj]
        return [floatify_coordinates(value) for value in obj]
    return obj


def normalize_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": fixture["name"],
        "geometry_type": fixture["geometry_type"],
        "coordinates": floatify_coordinates(fixture["coordinates"]),
        "valid": fixture["valid"],
    }


def normalize_stats(stats: dict[str, int]) -> dict[str, int]:
    return {key: stats[key] for key in STAT_KEYS}


def snapshot_digest(fixtures: list[dict[str, Any]], stats: dict[str, int]) -> str:
    body = {
        "fixtures": [normalize_fixture(fx) for fx in sorted(fixtures, key=lambda f: f["name"])],
        "stats": normalize_stats(stats),
    }
    payload = json.dumps(body, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def repair_binding(fixtures: list[dict[str, Any]], stats: dict[str, int]) -> str:
    digest = snapshot_digest(fixtures, stats)
    payload = f"repair\n{digest}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def unique_vertices(ring: list[list[float]]) -> list[list[float]]:
    if not ring:
        return []
    out = [ring[0]]
    for p in ring[1:]:
        if out[-1] == p:
            continue
        out.append(p)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


def signed_area(ring: list[list[float]]) -> float:
    verts = unique_vertices(ring)
    if len(verts) < 3:
        return 0.0
    total = 0.0
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return total * 0.5


def sanitize_ring(ring: list[list[float]]) -> tuple[list[list[float]], int]:
    if not ring:
        return ring, 0
    removed = 0
    out = [ring[0]]
    for p in ring[1:]:
        if out[-1] == p:
            removed += 1
            continue
        out.append(p)
    return out, removed


def normalize_close(ring: list[list[float]]) -> tuple[list[list[float]], int]:
    if not ring:
        return ring, 0
    normalized = 0
    out = list(ring)
    while len(out) > 1 and out[0] == out[-1]:
        out.pop()
        normalized += 1
    if out and (len(out) == 1 or out[-1] != out[0]):
        out.append(out[0][:])
    return out, normalized


def reverse_ring(ring: list[list[float]]) -> list[list[float]]:
    if len(ring) <= 1:
        return ring
    out = [p[:] for p in ring]
    out.reverse()
    return out


def point_in_ring(pt: list[float], ring: list[list[float]]) -> bool:
    x, y = pt
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
        ):
            inside = not inside
        j = i
    return inside


def ring_representative(ring: list[list[float]]) -> list[float]:
    n = max(len(ring) - 1, 1)
    sx = sum(p[0] for p in ring[:n])
    sy = sum(p[1] for p in ring[:n])
    return [sx / n, sy / n]


def nest_polygon(rings: list[list[list[float]]]) -> tuple[list[list[list[float]]], int]:
    if len(rings) <= 1:
        return rings, 0
    tagged = [(i, abs(signed_area(r)), r) for i, r in enumerate(rings)]
    tagged.sort(key=lambda t: t[1], reverse=True)
    exterior = tagged[0][2]
    holes: list[list[list[float]]] = []
    for _i, _area, ring in tagged[1:]:
        if point_in_ring(ring_representative(ring), exterior):
            holes.append(ring)
    out = [exterior, *holes]
    return out, 1 if len(out) > 1 else 0


def orient_polygon(rings: list[list[list[float]]]) -> tuple[list[list[list[float]]], int, int]:
    ext = 0
    intr = 0
    out: list[list[list[float]]] = []
    for idx, ring in enumerate(rings):
        area = signed_area(ring)
        r = ring
        if idx == 0:
            if area < 0:
                r = reverse_ring(ring)
                ext += 1
        else:
            if area > 0:
                r = reverse_ring(ring)
                intr += 1
        out.append(r)
    return out, ext, intr


def repair_ring(ring: list[list[float]], stats: dict[str, int]) -> list[list[float]]:
    r, dup = sanitize_ring(ring)
    stats["duplicate_vertices_removed"] += dup
    r, close = normalize_close(r)
    stats["closing_vertices_normalized"] += close
    return r


def repair_polygon(rings: list[list[list[float]]], stats: dict[str, int]) -> list[list[list[float]]]:
    repaired = [repair_ring(r, stats) for r in rings]
    nested, reordered = nest_polygon(repaired)
    stats["rings_reordered"] += reordered
    oriented, ext, intr = orient_polygon(nested)
    stats["exterior_reversed"] += ext
    stats["interior_reversed"] += intr
    return oriented


def repair_geometry(geometry: dict[str, Any], stats: dict[str, int]) -> dict[str, Any]:
    gtype = geometry["type"]
    if gtype == "Polygon":
        coords = repair_polygon(geometry["coordinates"], stats)
        return {"type": "Polygon", "coordinates": coords}
    if gtype == "MultiPolygon":
        stats["multipolygon_members"] += len(geometry["coordinates"])
        polys = [repair_polygon(poly, stats) for poly in geometry["coordinates"]]
        return {"type": "MultiPolygon", "coordinates": polys}
    raise ValueError(gtype)


def reference_report(fixture_dir: Path) -> dict[str, Any]:
    stats = {
        "fixtures_read": 0,
        "exterior_reversed": 0,
        "interior_reversed": 0,
        "duplicate_vertices_removed": 0,
        "closing_vertices_normalized": 0,
        "rings_reordered": 0,
        "multipolygon_members": 0,
    }
    fixtures: list[dict[str, Any]] = []
    for path in sorted(fixture_dir.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        stats["fixtures_read"] += 1
        repaired = repair_geometry(doc["geometry"], stats)
        fixtures.append(
            {
                "name": doc["name"],
                "geometry_type": repaired["type"],
                "coordinates": repaired["coordinates"],
                "valid": True,
            }
        )
    return {
        "report_version": 1,
        "valid": True,
        "fixtures": fixtures,
        "stats": stats,
        "repair_binding": repair_binding(fixtures, stats),
    }


def is_valid_ring(ring: list[list[float]], exterior: bool) -> bool:
    if len(ring) < 4 or ring[0] != ring[-1]:
        return False
    area = signed_area(ring)
    if exterior:
        return area > 0
    return area < 0


def validate_report(report: dict[str, Any]) -> bool:
    binding = report.get("repair_binding")
    if not binding:
        return False
    expected = repair_binding(report["fixtures"], report["stats"])
    if binding != expected:
        return False
    for fx in report["fixtures"]:
        coords = fx["coordinates"]
        if fx["geometry_type"] == "Polygon":
            if not coords or not is_valid_ring(coords[0], True):
                return False
            for hole in coords[1:]:
                if not is_valid_ring(hole, False):
                    return False
                if not point_in_ring(ring_representative(hole), coords[0]):
                    return False
        elif fx["geometry_type"] == "MultiPolygon":
            for poly in coords:
                if not poly or not is_valid_ring(poly[0], True):
                    return False
                for hole in poly[1:]:
                    if not is_valid_ring(hole, False):
                        return False
    return report.get("valid") is True
