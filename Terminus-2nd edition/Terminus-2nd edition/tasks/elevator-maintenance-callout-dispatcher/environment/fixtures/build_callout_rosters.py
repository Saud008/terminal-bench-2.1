#!/usr/bin/env python3
"""Build dispatch scenario bundles with randomized technician and building labels."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN_ROOT = os.environ.get("CALLOUTD_HIDDEN_ROOT")
TARGET = Path(HIDDEN_ROOT) if HIDDEN_ROOT else ROOT

BUNDLED = [
    "clean-dispatch",
    "trapped-escalation",
    "skill-floor-edge",
    "access-window-inclusive",
    "sla-tier-gold",
    "stable-order-tie",
    "cancelled-fault-skip",
    "locked-rerun",
]
HIDDEN = ["hidden-access-end-trap", "hidden-sla-tier-trap"]


def _rng(seed: str) -> random.Random:
    h = hashlib.sha256(seed.encode()).hexdigest()
    return random.Random(int(h[:12], 16))


def _tech(rng: random.Random, level: int, start: int, end: int) -> dict:
    return {
        "tech_id": f"T{rng.randint(1000, 9999)}",
        "skill_level": level,
        "shift_start": start,
        "shift_end": end,
        "cert_tags": ["elevator"],
    }


def _building(rng: random.Random, windows: list[dict]) -> dict:
    return {
        "building_id": f"B{rng.randint(10, 99)}",
        "access_windows": windows,
    }


def scenario_bundle(name: str, rng: random.Random, *, hidden: bool = False) -> dict:
    anchor = 600
    travel = 15
    tech_a = _tech(rng, 3, 480, 720)
    tech_b = _tech(rng, 2, 480, 720)
    bld_a = _building(rng, [{"start_minute": 500, "end_minute": 700}])
    sla_gold = {
        "tier": "gold",
        "building_id": bld_a["building_id"],
        "max_response_minutes": 90,
        "escalation_weight": 30,
        "tier_rank": 3,
    }
    sla_silver = {
        "tier": "silver",
        "building_id": bld_a["building_id"],
        "max_response_minutes": 120,
        "escalation_weight": 10,
        "tier_rank": 2,
    }
    base = {
        "seed": hashlib.sha256(f"{name}-{rng.random()}".encode()).hexdigest()[:16],
        "scenario": name,
        "roster_epoch_minute": anchor,
        "travel_buffer_minutes": travel,
        "technicians": [tech_a, tech_b],
        "buildings": [bld_a],
        "sla_contracts": [sla_gold, sla_silver],
        "faults": [],
    }

    if name == "clean-dispatch":
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "A",
                "fault_code": "DOOR-01",
                "severity_base": 2,
                "trapped_passengers": 0,
                "reported_minute": 550,
                "required_skill": 2,
                "cancelled": False,
            }
        ]
    elif name == "trapped-escalation":
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "B",
                "fault_code": "TRAP-09",
                "severity_base": 3,
                "trapped_passengers": 2,
                "reported_minute": 560,
                "required_skill": 2,
                "cancelled": False,
            }
        ]
    elif name == "skill-floor-edge":
        base["technicians"] = [tech_b, tech_a]
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "C",
                "fault_code": "CTRL-02",
                "severity_base": 2,
                "trapped_passengers": 0,
                "reported_minute": 555,
                "required_skill": 2,
                "cancelled": False,
            }
        ]
    elif name == "access-window-inclusive":
        bld_a["access_windows"] = [{"start_minute": 500, "end_minute": 570}]
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "D",
                "fault_code": "MOTOR-03",
                "severity_base": 2,
                "trapped_passengers": 0,
                "reported_minute": 555,
                "required_skill": 2,
                "cancelled": False,
            }
        ]
    elif name == "sla-tier-gold":
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "E",
                "fault_code": "SLA-01",
                "severity_base": 1,
                "trapped_passengers": 0,
                "reported_minute": 580,
                "required_skill": 2,
                "cancelled": False,
            }
        ]
    elif name == "stable-order-tie":
        f1 = f"F{rng.randint(100,499)}"
        f2 = f"F{rng.randint(500,999)}"
        base["technicians"] = [tech_a]
        base["faults"] = [
            {
                "fault_id": f2,
                "building_id": bld_a["building_id"],
                "elevator_bank": "G",
                "fault_code": "TIE-02",
                "severity_base": 2,
                "trapped_passengers": 0,
                "reported_minute": 550,
                "required_skill": 2,
                "cancelled": False,
            },
            {
                "fault_id": f1,
                "building_id": bld_a["building_id"],
                "elevator_bank": "F",
                "fault_code": "TIE-01",
                "severity_base": 2,
                "trapped_passengers": 0,
                "reported_minute": 550,
                "required_skill": 2,
                "cancelled": False,
            },
        ]
    elif name == "cancelled-fault-skip":
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,499)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "H",
                "fault_code": "CAN-01",
                "severity_base": 5,
                "trapped_passengers": 0,
                "reported_minute": 550,
                "required_skill": 2,
                "cancelled": True,
            },
            {
                "fault_id": f"F{rng.randint(500,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "I",
                "fault_code": "DOOR-02",
                "severity_base": 2,
                "trapped_passengers": 0,
                "reported_minute": 555,
                "required_skill": 2,
                "cancelled": False,
            },
        ]
    elif name == "locked-rerun":
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "J",
                "fault_code": "RERUN-01",
                "severity_base": 2,
                "trapped_passengers": 0,
                "reported_minute": 550,
                "required_skill": 2,
                "cancelled": False,
            }
        ]
    elif name == "hidden-access-end-trap":
        bld_a["access_windows"] = [{"start_minute": 500, "end_minute": 570}]
        base["roster_epoch_minute"] = 600
        base["travel_buffer_minutes"] = 15
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "Z",
                "fault_code": "HID-ACC",
                "severity_base": 3,
                "trapped_passengers": 0,
                "reported_minute": 555,
                "required_skill": 2,
                "cancelled": False,
            }
        ]
    elif name == "hidden-sla-tier-trap":
        base["sla_contracts"] = [sla_silver, sla_gold]
        base["faults"] = [
            {
                "fault_id": f"F{rng.randint(100,999)}",
                "building_id": bld_a["building_id"],
                "elevator_bank": "Y",
                "fault_code": "HID-SLA",
                "severity_base": 2,
                "trapped_passengers": 0,
                "reported_minute": 570,
                "required_skill": 2,
                "cancelled": False,
            }
        ]
    else:
        raise ValueError(name)

    return base


def write_bundle(name: str, bundle: dict) -> None:
    dest = TARGET / "scenarios" / name
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "bundle.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for name in BUNDLED:
        write_bundle(name, scenario_bundle(name, _rng(name)))
    for name in HIDDEN:
        write_bundle(name, scenario_bundle(name, _rng(name + "-hidden"), hidden=True))
    manifest = {"bundled": BUNDLED, "hidden": HIDDEN}
    (TARGET / "dispatch_scenarios.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
