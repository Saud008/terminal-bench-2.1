"""Independent NDP fouling trend contract math for rotrace chronicle publish."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def pick_field(batches: dict[str, dict[str, Any]], batch_id: str, field: str) -> float:
    cur = batch_id
    while cur in batches:
        batch = batches[cur]
        val = batch.get(field)
        if val is not None:
            return float(val)
        parent = batch.get("parent_batch_id")
        if not parent:
            break
        cur = parent
    defaults = {"alpha": 1.0, "beta": 1.0, "p_base": 0.0, "t_ref": 25.0, "q_ref": 100.0}
    return defaults[field]


def batch_for_hour(hour: int, batches: list[dict[str, Any]]) -> str:
    for row in batches:
        if row["active_from_hour"] <= hour <= row["active_until_hour"]:
            return row["batch_id"]
    return ""


def apply_cal_offset(salinity: float, offset: float) -> float:
    return salinity - offset


def bridge_readings(readings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_rows = sorted(readings, key=lambda r: r["hour_index"])
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(sorted_rows):
        r = dict(row)
        flags = row.get("sensor_flags", "")
        if "salinity_dropout" in flags:
            prev = sorted_rows[idx - 1] if idx > 0 else None
            if prev is not None:
                r["salinity_ppt"] = prev["salinity_ppt"]
        if "pressure_dropout" in flags:
            prev = sorted_rows[idx - 1] if idx > 0 else None
            nxt = sorted_rows[idx + 1] if idx + 1 < len(sorted_rows) else None
            if prev and nxt:
                span = nxt["hour_index"] - prev["hour_index"]
                frac = (row["hour_index"] - prev["hour_index"]) / span
                r["pressure_bar"] = prev["pressure_bar"] + frac * (nxt["pressure_bar"] - prev["pressure_bar"])
        if "flow_dropout" in flags:
            prev = sorted_rows[idx - 1] if idx > 0 else None
            nxt = sorted_rows[idx + 1] if idx + 1 < len(sorted_rows) else None
            if prev and nxt:
                span = nxt["hour_index"] - prev["hour_index"]
                frac = (row["hour_index"] - prev["hour_index"]) / span
                r["flow_m3h"] = prev["flow_m3h"] + frac * (nxt["flow_m3h"] - prev["flow_m3h"])
        out.append(r)
    return out


def compute_ndp(
    pressure: float,
    p_base: float,
    temp: float,
    t_ref: float,
    flow: float,
    q_ref: float,
    alpha: float,
    beta: float,
    salinity: float,
) -> float:
    dp = pressure - p_base
    brine = 1.0 + salinity / 1000.0
    return dp * (t_ref / temp) ** alpha * (q_ref / flow) ** beta * brine


def classify_slope(ndp_series: list[float]) -> str:
    if len(ndp_series) < 2:
        return "stable"
    slope = (ndp_series[-1] - ndp_series[0]) / (len(ndp_series) - 1)
    if slope <= 0.01:
        return "stable"
    if slope <= 0.05:
        return "accelerating"
    return "critical"


def element_fp(batch_id: str, hour: int, salinity: float, pressure: float) -> str:
    body = f"{batch_id}:{hour}:{salinity:.3f}:{pressure:.3f}".encode()
    return hashlib.sha256(body).hexdigest()[:16]


def severity_rank(trend: str) -> int:
    return {"critical": 0, "accelerating": 1, "stable": 2}.get(trend, 3)


def contract_lineage_digest(batches: list[dict[str, Any]]) -> str:
    pairs = sorted(f"{b['batch_id']}:{b.get('parent_batch_id') or ''}" for b in batches)
    return hashlib.sha256("|".join(pairs).encode()).hexdigest()


def load_readings_csv(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cols = ln.split(",")
        out.append(
            {
                "hour_index": int(cols[0]),
                "batch_id": cols[1],
                "pressure_bar": float(cols[2]),
                "salinity_ppt": float(cols[3]),
                "flow_m3h": float(cols[4]),
                "temperature_c": float(cols[5]),
                "sensor_flags": cols[6],
                "cal_offset_ppt": float(cols[7]),
            }
        )
    return out


def load_cleaning_csv(path: Path) -> list[dict[str, Any]]:
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        if not ln.strip():
            continue
        cols = ln.split(",")
        out.append({"hour_index": int(cols[0]), "event_type": cols[1], "cleaned_on": cols[2]})
    return out


def load_batches(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))["batches"]


def apply_cal_table(readings: list[dict[str, Any]], cal_path: Path | None) -> list[dict[str, Any]]:
    if cal_path is None or not cal_path.is_file():
        return readings
    overrides: dict[int, float] = {}
    for ln in cal_path.read_text(encoding="utf-8").splitlines()[1:]:
        if not ln.strip():
            continue
        cols = ln.split(",")
        overrides[int(cols[0])] = float(cols[1])
    out = []
    for row in readings:
        patched = dict(row)
        if row["hour_index"] in overrides:
            patched["cal_offset_ppt"] = overrides[row["hour_index"]]
        out.append(patched)
    return out


def contract_chronicle(
    run_id: str,
    train_id: str,
    readings: list[dict[str, Any]],
    batches: list[dict[str, Any]],
    cleaning: list[dict[str, Any]],
) -> dict[str, Any]:
    batch_map = {b["batch_id"]: b for b in batches}
    p_base_map = {b["batch_id"]: float(b["p_base"]) for b in batches if b.get("p_base") is not None}
    bridged = bridge_readings(readings)
    ndp_series: list[float] = []
    rows: list[dict[str, Any]] = []
    for row in bridged:
        hour = row["hour_index"]
        bid = batch_for_hour(hour, batches) or row["batch_id"]
        alpha = pick_field(batch_map, bid, "alpha")
        beta = pick_field(batch_map, bid, "beta")
        t_ref = pick_field(batch_map, bid, "t_ref")
        q_ref = pick_field(batch_map, bid, "q_ref")
        for ev in cleaning:
            if hour == ev["hour_index"]:
                p_base_map[bid] = row["pressure_bar"]
        p_base = p_base_map.get(bid, pick_field(batch_map, bid, "p_base"))
        sal = apply_cal_offset(row["salinity_ppt"], row["cal_offset_ppt"])
        ndp = round(
            compute_ndp(
                row["pressure_bar"],
                p_base,
                row["temperature_c"],
                t_ref,
                row["flow_m3h"],
                q_ref,
                alpha,
                beta,
                sal,
            ),
            4,
        )
        ndp_series.append(ndp)
        trend = classify_slope(ndp_series)
        rows.append(
            {
                "hour_index": hour,
                "batch_id": bid,
                "ndp": ndp,
                "trend_class": trend,
                "element_fp": element_fp(bid, hour, sal, row["pressure_bar"]),
            }
        )
    rows.sort(key=lambda r: (severity_rank(r["trend_class"]), r["hour_index"]))
    summary = {
        "total_readings": len(rows),
        "critical_count": sum(1 for r in rows if r["trend_class"] == "critical"),
        "accelerating_count": sum(1 for r in rows if r["trend_class"] == "accelerating"),
        "stable_count": sum(1 for r in rows if r["trend_class"] == "stable"),
        "max_ndp": max((r["ndp"] for r in rows), default=0.0),
    }
    ndp_values = sorted(round(r["ndp"], 4) for r in rows)
    digest_body = json.dumps(
        {
            "accelerating_count": summary["accelerating_count"],
            "critical_count": summary["critical_count"],
            "max_ndp": summary["max_ndp"],
            "ndp_values": ndp_values,
            "stable_count": summary["stable_count"],
            "total_readings": summary["total_readings"],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        "run_id": run_id,
        "train_id": train_id,
        "chronicle_rows": rows,
        "summary": summary,
        "batch_lineage_digest": contract_lineage_digest(batches),
        "chronicle_digest": hashlib.sha256(digest_body.encode()).hexdigest(),
    }


# Verifier gate expects reference_* entry points for independent contract math.
reference_chronicle = contract_chronicle
reference_lineage_digest = contract_lineage_digest
