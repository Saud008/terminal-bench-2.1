#!/usr/bin/env python3
"""Build randomized plant shift fixtures with stable seed."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def dual_chem_basic(rng: random.Random) -> dict:
    fm = "FM-" + str(rng.randint(10, 99))
    tu = "TU-" + str(rng.randint(1, 9))
    return {
        "plant_id": "plant-north-alpha",
        "shift": "dual-chem-basic",
        "as_of": "2026-04-01T06:00:00Z",
        "target_turbidity_ntu": 1.0,
        "min_flow_lpm": 50.0,
        "minute_dose_cap_mg": 1000000.0,
        "chemicals": [
            {"chem_id": "ALUM-A", "lot_code": "LOT-881", "unit": "mg/L", "concentration": 25.0, "max_dose_mg": 8000.0},
            {"chem_id": "CL2-X", "lot_code": "LOT-442", "unit": "ppm", "concentration": 12.0, "max_dose_mg": 5000.0},
        ],
        "flow_readings": [
            {"sensor_id": fm, "minute": 0, "m3_h": 120.0, "status": "ok"},
            {"sensor_id": fm, "minute": 1, "m3_h": 118.0, "status": "ok"},
            {"sensor_id": fm, "minute": 2, "m3_h": 121.0, "status": "ok"},
        ],
        "turbidity_readings": [
            {"sensor_id": tu, "minute": 0, "ntu": 0.8, "status": "ok"},
            {"sensor_id": tu, "minute": 1, "ntu": 1.2, "status": "ok"},
            {"sensor_id": tu, "minute": 2, "ntu": 1.5, "status": "ok"},
        ],
        "overrides": [],
    }


def outage_forward_fill(rng: random.Random) -> dict:
    sid = "FM-" + str(rng.randint(20, 40))
    return {
        "plant_id": "plant-east-gamma",
        "shift": "outage-forward-fill",
        "as_of": "2026-04-02T00:00:00Z",
        "target_turbidity_ntu": 1.0,
        "min_flow_lpm": 50.0,
        "minute_dose_cap_mg": 1000000.0,
        "chemicals": [
            {"chem_id": "POLY-P1", "lot_code": "LOT-991", "unit": "mg/L", "concentration": 10.0, "max_dose_mg": 12000.0},
        ],
        "flow_readings": [
            {"sensor_id": sid, "minute": 0, "m3_h": 60.0, "status": "ok"},
            {"sensor_id": sid, "minute": 1, "m3_h": 0.0, "status": "outage"},
            {"sensor_id": sid, "minute": 2, "m3_h": 0.0, "status": "outage"},
            {"sensor_id": sid, "minute": 3, "m3_h": 62.0, "status": "ok"},
        ],
        "turbidity_readings": [
            {"sensor_id": "TU-3", "minute": 0, "ntu": 1.0, "status": "ok"},
            {"sensor_id": "TU-3", "minute": 1, "ntu": 0.0, "status": "outage"},
            {"sensor_id": "TU-3", "minute": 2, "ntu": 0.0, "status": "outage"},
            {"sensor_id": "TU-3", "minute": 3, "ntu": 1.1, "status": "ok"},
        ],
        "overrides": [],
    }


def override_role_mix(rng: random.Random) -> dict:
    return {
        "plant_id": "plant-west-delta",
        "shift": "override-role-mix",
        "as_of": "2026-04-03T12:00:00Z",
        "target_turbidity_ntu": 1.0,
        "min_flow_lpm": 50.0,
        "minute_dose_cap_mg": 1000000.0,
        "chemicals": [
            {"chem_id": "LIME-L1", "lot_code": "LOT-331", "unit": "mg/L", "concentration": 30.0, "max_dose_mg": 6000.0},
        ],
        "flow_readings": [
            {"sensor_id": "FM-55", "minute": 0, "m3_h": 90.0, "status": "ok"},
            {"sensor_id": "FM-55", "minute": 1, "m3_h": 92.0, "status": "ok"},
        ],
        "turbidity_readings": [
            {"sensor_id": "TU-7", "minute": 0, "ntu": 0.9, "status": "ok"},
            {"sensor_id": "TU-7", "minute": 1, "ntu": 0.95, "status": "ok"},
        ],
        "overrides": [
            {"user": "op." + rng.choice(["smith", "lee"]), "role": "Supervisor", "chem_id": "LIME-L1", "factor": 1.15},
            {"user": "guest.temp", "role": "supervisor", "chem_id": "LIME-L1", "factor": 2.0},
        ],
    }


def turbidity_uplift_cap(rng: random.Random) -> dict:
    return {
        "plant_id": "plant-south-epsilon",
        "shift": "turbidity-uplift-cap",
        "as_of": "2026-04-04T18:00:00Z",
        "target_turbidity_ntu": 1.0,
        "min_flow_lpm": 50.0,
        "minute_dose_cap_mg": 1000000.0,
        "chemicals": [
            {"chem_id": "COAG-C9", "lot_code": "LOT-777", "unit": "mg/L", "concentration": 20.0, "max_dose_mg": 50000.0},
        ],
        "flow_readings": [
            {"sensor_id": "FM-88", "minute": 0, "m3_h": 100.0, "status": "ok"},
        ],
        "turbidity_readings": [
            {"sensor_id": "TU-2", "minute": 0, "ntu": 8.0, "status": "ok"},
        ],
        "overrides": [],
    }


def percent_unit_lot(rng: random.Random) -> dict:
    return {
        "plant_id": "plant-central-zeta",
        "shift": "percent-unit-lot",
        "as_of": "2026-04-05T08:00:00Z",
        "target_turbidity_ntu": 1.0,
        "min_flow_lpm": 50.0,
        "minute_dose_cap_mg": 1000000.0,
        "chemicals": [
            {"chem_id": "ACID-H2", "lot_code": "LOT-101", "unit": "percent", "concentration": 0.05, "max_dose_mg": 200000.0},
        ],
        "flow_readings": [
            {"sensor_id": "FM-12", "minute": 0, "m3_h": 75.0, "status": "ok"},
            {"sensor_id": "FM-12", "minute": 1, "m3_h": 76.0, "status": "ok"},
        ],
        "turbidity_readings": [
            {"sensor_id": "TU-4", "minute": 0, "ntu": 1.0, "status": "ok"},
            {"sensor_id": "TU-4", "minute": 1, "ntu": 1.0, "status": "ok"},
        ],
        "overrides": [],
    }


BUILDERS = {
    "dual-chem-basic": dual_chem_basic,
    "outage-forward-fill": outage_forward_fill,
    "override-role-mix": override_role_mix,
    "turbidity-uplift-cap": turbidity_uplift_cap,
    "percent-unit-lot": percent_unit_lot,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=4821)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    registry = []
    for name, fn in BUILDERS.items():
        bundle = fn(rng)
        bundle["shift"] = name
        (args.out_dir / f"{name}.json").write_text(
            json.dumps(bundle, indent=2) + "\n", encoding="utf-8"
        )
        registry.append({"shift": name, "plant_id": bundle["plant_id"]})
    (args.out_dir / "shift_registry.json").write_text(
        json.dumps({"shifts": registry}, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
