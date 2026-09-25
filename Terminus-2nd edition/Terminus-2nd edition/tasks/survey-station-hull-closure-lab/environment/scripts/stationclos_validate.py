#!/usr/bin/env python3
"""Independent validation math for stationclos residual closure."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


def load_config(path: str = "/app/config/stationclos.json") -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    env = os.environ.get("TB3_MICRO_SCALE")
    if env:
        try:
            n = int(env)
            if n > 0:
                cfg["microdegree_scale"] = n
        except ValueError:
            pass
    return cfg


def apply_residual(vertices: list[list[float]], datum: dict[str, float]) -> list[list[float]]:
    return [[v[0] - datum["lon"], v[1] - datum["lat"]] for v in vertices]


def quantize_coord(v: float, scale: int) -> float:
    return math.trunc(v * scale) / scale


def partition_wrap(station_id: str, residual: list[list[float]]) -> list[tuple[str, list[list[float]]]]:
    if len(residual) < 3:
        return [(station_id, residual)]
    crosses = False
    for i in range(len(residual) - 1):
        if abs(residual[i + 1][0] - residual[i][0]) > 180.0:
            crosses = True
            break
    if not crosses:
        return [(station_id, residual)]
    west = [v for v in residual if v[0] >= 0.0]
    east = [v for v in residual if v[0] < 0.0]
    out: list[tuple[str, list[list[float]]]] = []
    if len(west) >= 3:
        out.append((f"{station_id}-W", west))
    if len(east) >= 3:
        out.append((f"{station_id}-E", east))
    if not out:
        out.append((station_id, residual))
    return out


def bbox_of(verts: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    return min(xs), min(ys), max(xs), max(ys)


def area_u64(min_x: float, min_y: float, max_x: float, max_y: float, scale: int) -> int:
    dx = max_x - min_x
    dy = max_y - min_y
    if dx <= 0.0 or dy <= 0.0:
        return 0
    sx = int(round(dx * scale))
    sy = int(round(dy * scale))
    if sx <= 0 or sy <= 0:
        return 0
    return sx * sy


def open_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        a["min_x"] < b["max_x"]
        and b["min_x"] < a["max_x"]
        and a["min_y"] < b["max_y"]
        and b["min_y"] < a["max_y"]
    )


def build_stations(bundle: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    scale = int(cfg["microdegree_scale"])
    datum = cfg["datum_offset"]
    expanded: list[tuple[str, list[list[float]]]] = []
    for st in bundle["stations"]:
        residual = apply_residual(st["vertices"], datum)
        expanded.extend(partition_wrap(st["station_id"], residual))
    stations: list[dict[str, Any]] = []
    for sid, verts in expanded:
        q = [[quantize_coord(v[0], scale), quantize_coord(v[1], scale)] for v in verts]
        min_x, min_y, max_x, max_y = bbox_of(q)
        area = area_u64(min_x, min_y, max_x, max_y, scale)
        stations.append(
            {
                "station_id": sid,
                "residual_vertices": verts,
                "quantized_vertices": q,
                "min_x": min_x,
                "min_y": min_y,
                "max_x": max_x,
                "max_y": max_y,
                "residual_area_u64": area,
                "vertex_count": len(q),
            }
        )
    return stations


def first_conflict(stations: list[dict[str, Any]]) -> tuple[str, str] | None:
    for i in range(len(stations)):
        for j in range(i + 1, len(stations)):
            a, b = stations[i], stations[j]
            if a["residual_area_u64"] > 0 and b["residual_area_u64"] > 0 and open_overlap(a, b):
                return a["station_id"], b["station_id"]
    return None


def rank_stations(stations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "station_id": s["station_id"],
            "residual_area_u64": s["residual_area_u64"],
            "vertex_count": s["vertex_count"],
        }
        for s in stations
    ]
    rows.sort(key=lambda r: (r["residual_area_u64"], r["station_id"]))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    return rows


def closure_digest(rows: list[dict[str, Any]]) -> str:
    lines = [f"{r['station_id']}|{r['residual_area_u64']}|{r['vertex_count']}" for r in rows]
    body = "\n".join(lines)
    return hashlib.sha256(body.encode()).hexdigest()


def expected_atlas(campaign_id: str, bundle: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any] | None:
    stations = build_stations(bundle, cfg)
    if first_conflict(stations) is not None:
        return None
    rows = rank_stations(stations)
    areas = [r["residual_area_u64"] for r in rows]
    digest = closure_digest(rows)
    return {
        "campaign_id": campaign_id,
        "rows": rows,
        "summary": {
            "total_stations": len(rows),
            "wrap_parts": sum(
                1 for r in rows if r["station_id"].endswith("-W") or r["station_id"].endswith("-E")
            ),
            "max_area": max(areas) if areas else 0,
            "min_area": min(areas) if areas else 0,
        },
        "closure_digest": digest,
    }


def load_bundle(bundle_dir: str, name: str) -> dict[str, Any]:
    return json.loads(Path(bundle_dir, f"{name}.json").read_text(encoding="utf-8"))
