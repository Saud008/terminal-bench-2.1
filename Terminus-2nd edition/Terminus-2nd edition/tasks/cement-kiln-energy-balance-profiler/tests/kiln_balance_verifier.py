"""Independent thermodynamic reference layer for cement kiln heat balance verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

KCAL_TO_MJ = 0.004184
SPECIFIC_HEAT_MJ_PER_T = 1.75
GRID_STEP_SEC = 300


def celsius_from_probe(raw: float, unit: str) -> float:
    if unit.upper().startswith("K"):
        return raw - 273.15
    return raw


def calibrated_celsius(norm_c: float, offset_c: float) -> float:
    return norm_c - offset_c


def fuel_energy_mj(mass_kg: float, cv_kcal_kg: float) -> float:
    return mass_kg * cv_kcal_kg * KCAL_TO_MJ


def parse_csv_rows(path: Path, skip_header: bool = True) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if skip_header and lines:
        lines = lines[1:]
    return [ln.split(",") for ln in lines if ln.strip()]


def load_telemetry_rows(path: Path) -> list[dict]:
    out = []
    for cols in parse_csv_rows(path):
        out.append(
            {
                "probe_id": cols[0],
                "probe_ts": int(cols[1]),
                "temp_raw": float(cols[2]),
                "unit": cols[3],
                "cal_offset_c": float(cols[4]),
            }
        )
    return out


def load_fuel_rows(path: Path) -> list[dict]:
    out = []
    for cols in parse_csv_rows(path):
        mass = float(cols[2])
        cv = float(cols[3])
        out.append(
            {
                "batch_id": cols[0],
                "fuel_name": cols[1],
                "mass_kg": mass,
                "cv_kcal_kg": cv,
                "start_ts": int(cols[4]),
                "end_ts": int(cols[5]),
                "energy_mj": fuel_energy_mj(mass, cv),
            }
        )
    return out


def load_clinker_rows(path: Path) -> list[dict]:
    out = []
    for cols in parse_csv_rows(path):
        out.append(
            {
                "window_id": cols[0],
                "batch_id": cols[1],
                "clinker_t": float(cols[2]),
                "start_ts": int(cols[3]),
                "end_ts": int(cols[4]),
            }
        )
    return out


def lineage_batch(batches: list[dict], ts: int) -> str:
    for row in batches:
        if row["start_ts"] <= ts <= row["end_ts"]:
            return row["batch_id"]
    return ""


def reference_probe_timeline(
    telemetry: list[dict],
    batches: list[dict],
    cal_overrides: dict[str, float] | None = None,
) -> list[dict]:
    cal_overrides = cal_overrides or {}
    samples: list[tuple[int, str, float]] = []
    for row in telemetry:
        off = cal_overrides.get(row["probe_id"], row["cal_offset_c"])
        norm = celsius_from_probe(row["temp_raw"], row["unit"])
        samples.append((row["probe_ts"], row["probe_id"], calibrated_celsius(norm, off)))
    if not samples:
        return []
    samples.sort(key=lambda item: item[0])
    lo, hi = samples[0][0], samples[-1][0]
    timeline: list[dict] = []
    ts = lo
    while ts <= hi:
        hit = next((s for s in samples if s[0] == ts), None)
        if hit:
            _, pid, temp = hit
            interpolated = False
        else:
            before = [s for s in samples if s[0] < ts]
            after = [s for s in samples if s[0] > ts]
            if not before or not after:
                ts += GRID_STEP_SEC
                continue
            left, right = before[-1], after[0]
            ratio = (ts - left[0]) / (right[0] - left[0])
            temp = left[2] + ratio * (right[2] - left[2])
            pid = left[1]
            interpolated = True
        timeline.append(
            {
                "probe_ts": ts,
                "probe_id": pid,
                "temp_c": temp,
                "batch_id": lineage_batch(batches, ts),
                "interpolated": interpolated,
            }
        )
        ts += GRID_STEP_SEC
    return timeline


def reference_heat_balance(fuels: list[dict], clinker: list[dict], heat_loss_mj: float) -> dict:
    energy_in = sum(r["energy_mj"] for r in fuels)
    tonnes = sum(r["clinker_t"] for r in clinker)
    sink = sum(r["clinker_t"] * SPECIFIC_HEAT_MJ_PER_T for r in clinker)
    residual = energy_in - sink - heat_loss_mj
    return {
        "energy_in_mj": energy_in,
        "clinker_out_t": tonnes,
        "heat_loss_mj": heat_loss_mj,
        "residual_mj": residual,
        "residual_mj_per_t": residual / tonnes if tonnes else 0.0,
    }


def reference_lineage_digest(probes: list[dict]) -> str:
    body = "|".join(sorted(f"{p['probe_ts']}:{p['batch_id']}" for p in probes))
    return hashlib.sha256(body.encode()).hexdigest()


def reference_audit_digest(ledger: dict) -> str:
    payload = json.dumps(
        {
            "clinker_out_t": ledger["clinker_out_t"],
            "energy_in_mj": ledger["energy_in_mj"],
            "heat_loss_mj": ledger["heat_loss_mj"],
            "lineage_digest": ledger["lineage_digest"],
            "residual_mj_per_t": ledger["residual_mj_per_t"],
            "run_id": ledger["run_id"],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()
