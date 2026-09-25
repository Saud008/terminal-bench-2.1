"""Independent vibration compliance math for seismocomply."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


def dist_m(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


def closest_vertex_distance(blast: tuple[float, float], vertices: list[list[float]]) -> float:
    bx, by = blast
    return min(dist_m(bx, by, vx, vy) for vx, vy in vertices)


def attenuated_ppv(source: float, distance_m: float, ref_m: float, exponent: float) -> float:
    if distance_m <= 0.0:
        return source
    return source * (ref_m / distance_m) ** exponent


def corrected_ppv(raw: float, zero_offset: float, gain: float) -> float:
    return (raw - zero_offset) * gain


def local_hour(fired_at: str, tz_hours: int) -> int:
    hour = int(fired_at[11:13])
    return (hour + tz_hours) % 24


def pick_threshold(structure: str, fired_at: str, limits: dict[str, Any], tz_hours: int, scale: float) -> float:
    pair = limits.get(structure, limits["residential"])
    h = local_hour(fired_at, tz_hours)
    base = pair["day_mm_s"] if 7 <= h <= 18 else pair["night_mm_s"]
    return base * scale


def scoped_audit_id(seed: str, survey: str, seq: int) -> str:
    body = f"{seed}:{survey}:{seq}".encode()
    return "audit-" + hashlib.sha256(body).hexdigest()[:12]


def reference_atlas(
    seed: str,
    survey_name: str,
    record: dict[str, Any],
    correlate_seq: int,
    *,
    limit_scale: float = 1.0,
) -> dict[str, Any]:
    sensors = {s["sensor_id"]: s for s in record["sensors"]}
    properties = {p["property_id"]: p for p in record["properties"]}
    blasts = {b["blast_id"]: b for b in record["blasts"]}
    rows: list[dict[str, Any]] = []
    for reading in record["readings"]:
        blast = blasts[reading["blast_id"]]
        sensor = sensors[reading["sensor_id"]]
        parcel = properties[sensor["property_id"]]
        distance_m = closest_vertex_distance(
            (blast["easting_m"], blast["northing_m"]),
            parcel["boundary_vertices"],
        )
        att = attenuated_ppv(
            blast["source_ppv_mm_s"],
            distance_m,
            record["reference_distance_m"],
            record["attenuation_exponent"],
        )
        corr = corrected_ppv(
            reading["raw_ppv_mm_s"],
            sensor["zero_offset_mm_s"],
            sensor["gain_multiplier"],
        )
        combined = round(max(corr, att), 4)
        threshold = pick_threshold(
            parcel["structure_class"],
            blast["fired_at"],
            record["limits"],
            record["timezone_offset_hours"],
            limit_scale,
        )
        exceedance = round(max(0.0, combined - threshold), 4)
        rows.append(
            {
                "blast_id": reading["blast_id"],
                "property_id": sensor["property_id"],
                "sensor_id": reading["sensor_id"],
                "distance_m": round(distance_m, 3),
                "attenuated_ppv_mm_s": combined,
                "threshold_mm_s": threshold,
                "exceedance_mm_s": exceedance,
                "exceeded": exceedance > 0.0,
            }
        )
    rows.sort(key=lambda r: (r["property_id"], r["blast_id"], r["sensor_id"]))
    summary = {
        "reading_pairs": len(rows),
        "exceedance_count": sum(1 for r in rows if r["exceeded"]),
        "max_exceedance_mm_s": max((r["exceedance_mm_s"] for r in rows), default=0.0),
    }
    exceedance_values = sorted(round(r["exceedance_mm_s"], 4) for r in rows)
    digest_body = json.dumps(
        {
            "reading_pairs": summary["reading_pairs"],
            "exceedance_count": summary["exceedance_count"],
            "max_exceedance_mm_s": summary["max_exceedance_mm_s"],
            "exceedance_values": exceedance_values,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        "seed": seed,
        "survey": survey_name,
        "audit_run_id": scoped_audit_id(seed, survey_name, correlate_seq),
        "exceedance_rows": rows,
        "summary": summary,
        "atlas_digest": hashlib.sha256(digest_body.encode()).hexdigest(),
    }


def load_survey(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
