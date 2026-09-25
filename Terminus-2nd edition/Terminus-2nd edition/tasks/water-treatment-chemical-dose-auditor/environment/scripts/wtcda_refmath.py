#!/usr/bin/env python3
"""Independent reference for wtcdctl plant shift validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MAX_FORWARD_FILL = 3
AUTHORIZED_ROLES = ["supervisor", "chief-operator"]
DENYLIST = ["guest.temp"]


def arc_ppm_fingerprint(chem_id: str, lot_code: str, as_of: str) -> str:
    body = f"{chem_id}:{lot_code}:{as_of}".encode()
    return hashlib.sha256(body).hexdigest()[:16]


def normalize_mg_per_l(value: float, unit: str) -> float:
    if unit == "mg/L" or unit == "ppm":
        return value
    if unit == "percent":
        return value * 10000.0
    return value


def m3h_to_lpm(m3_h: float) -> float:
    return m3_h * 1000.0 / 60.0


def turbidity_uplift(turbidity_ntu: float, target_ntu: float) -> float:
    if turbidity_ntu <= target_ntu:
        return 1.0
    raw = 1.0 + (turbidity_ntu - target_ntu) / target_ntu * 0.10
    return min(raw, 1.5)


def flow_weighted_mg_per_l(concentrations: list[float], flows: list[float]) -> float:
    if not concentrations or not flows:
        return 0.0
    num = sum(c * f for c, f in zip(concentrations, flows))
    den = sum(flows)
    return num / den if den > 0 else 0.0


def override_allowed(user: str, role: str) -> bool:
    if user in DENYLIST:
        return False
    role_lower = role.lower()
    return any(r.lower() == role_lower for r in AUTHORIZED_ROLES)


def forward_fill(values: list[float | None]) -> list[float]:
    out: list[float] = []
    last: float | None = None
    gap = 0
    for v in values:
        if v is not None:
            last = v
            gap = 0
            out.append(v)
        else:
            gap += 1
            if gap <= MAX_FORWARD_FILL and last is not None:
                out.append(last)
            else:
                out.append(0.0)
    return out


def build_minute_series(
    readings: list[dict[str, Any]], value_key: str, scale_fn
) -> dict[int, float]:
    by_sensor: dict[str, list[tuple[int, float | None]]] = {}
    for r in readings:
        val = scale_fn(r) if r.get("status") == "ok" else None
        by_sensor.setdefault(r["sensor_id"], []).append((r["minute"], val))
    out: dict[int, float] = {}
    for rows in by_sensor.values():
        rows.sort(key=lambda x: x[0])
        filled = forward_fill([v for _, v in rows])
        for i, (minute, _) in enumerate(rows):
            out[minute] = filled[i]
    return out


def minute_eligible(flow_lpm: float, min_flow_lpm: float) -> bool:
    return flow_lpm >= min_flow_lpm


def apply_minute_cap(dose_mg: float, cap_mg: float) -> float:
    return min(dose_mg, cap_mg)


def compute_chemical_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    flow_by_min = build_minute_series(
        bundle["flow_readings"],
        "m3_h",
        lambda r: m3h_to_lpm(float(r["m3_h"])),
    )
    turb_by_min = build_minute_series(
        bundle["turbidity_readings"],
        "ntu",
        lambda r: float(r["ntu"]),
    )
    max_min = max([*flow_by_min.keys(), *turb_by_min.keys()], default=0)
    min_flow = float(bundle.get("min_flow_lpm", 0.0))
    minute_cap = float(bundle.get("minute_dose_cap_mg", 1e18))
    rows: list[dict[str, Any]] = []
    for chem in bundle["chemicals"]:
        concs: list[float] = []
        flows: list[float] = []
        total = 0.0
        contact_excluded = 0
        override_applied = False
        for minute in range(max_min + 1):
            flow = flow_by_min.get(minute, 0.0)
            if not minute_eligible(flow, min_flow):
                contact_excluded += 1
                continue
            turb = turb_by_min.get(minute, bundle["target_turbidity_ntu"])
            conc = normalize_mg_per_l(float(chem["concentration"]), chem["unit"])
            for ov in bundle.get("overrides", []):
                if ov["chem_id"] == chem["chem_id"] and override_allowed(ov["user"], ov["role"]):
                    conc *= float(ov["factor"])
                    override_applied = True
            uplift = turbidity_uplift(turb, float(bundle["target_turbidity_ntu"]))
            raw = flow * conc * uplift
            total += apply_minute_cap(raw, minute_cap)
            concs.append(conc)
            flows.append(flow)
        rows.append(
            {
                "chem_id": chem["chem_id"],
                "arc_tok": arc_ppm_fingerprint(
                    chem["chem_id"], chem["lot_code"], bundle["as_of"]
                ),
                "weighted_conc_mg_l": flow_weighted_mg_per_l(concs, flows),
                "total_dose_mg": total,
                "max_dose_mg": float(chem["max_dose_mg"]),
                "contact_excluded_minutes": contact_excluded,
                "override_applied": override_applied,
            }
        )
    return rows


def breach_atlas_seal(summary: dict[str, Any]) -> str:
    body = json.dumps(
        {
            "breach_count": summary["breach_count"],
            "chemical_count": summary["chemical_count"],
            "max_severity_pct": summary["max_severity_pct"],
            "plant_id": summary["plant_id"],
            "shift": summary["shift"],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def revision_token(plant_id: str, shift: str, as_of: str) -> str:
    body = f"{plant_id}:{shift}:{as_of}".encode()
    return hashlib.sha256(body).hexdigest()[:12]


def reference_safety(
    plant_id: str,
    shift: str,
    bundle_path: Path,
) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    chemicals = compute_chemical_rows(bundle)
    breaches = []
    for c in chemicals:
        if c["total_dose_mg"] > c["max_dose_mg"]:
            severity = (c["total_dose_mg"] - c["max_dose_mg"]) / c["max_dose_mg"] * 100.0
            breaches.append(
                {
                    "chem_id": c["chem_id"],
                    "total_dose_mg": c["total_dose_mg"],
                    "max_dose_mg": c["max_dose_mg"],
                    "severity_pct": severity,
                }
            )
    breaches.sort(key=lambda r: (-r["severity_pct"], r["chem_id"]))
    summary = {
        "plant_id": plant_id,
        "shift": shift,
        "chemical_count": len(chemicals),
        "breach_count": len(breaches),
        "max_severity_pct": breaches[0]["severity_pct"] if breaches else 0.0,
    }
    return {
        "plant_id": plant_id,
        "shift": shift,
        "rows": breaches,
        "summary": summary,
        "breach_atlas_seal": breach_atlas_seal(summary),
        "_ledger": {
            "ledger_revision_token": revision_token(plant_id, shift, bundle["as_of"]),
            "plant_id": plant_id,
            "shift": shift,
            "as_of": bundle["as_of"],
            "chemicals": chemicals,
        },
    }
