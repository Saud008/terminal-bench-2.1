#!/usr/bin/env python3
"""Generate randomized municipal permit scenario bundles."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "scenarios"
SEED = 0x4D504951  # MPIQ


def _rng(scenario: str) -> random.Random:
    h = hashlib.sha256(f"{SEED}:{scenario}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _routes() -> list[dict]:
    return [
        {"permit_type": "building-residential", "inspection_lane": "lane-structural", "min_cert_level": 2},
        {"permit_type": "building-commercial", "inspection_lane": "lane-structural", "min_cert_level": 3},
        {"permit_type": "electrical-service", "inspection_lane": "lane-electrical", "min_cert_level": 3},
        {"permit_type": "electrical-renewal", "inspection_lane": "lane-electrical", "min_cert_level": 2},
        {"permit_type": "plumbing-major", "inspection_lane": "lane-plumbing", "min_cert_level": 2},
        {"permit_type": "zoning-variance", "inspection_lane": "lane-zoning", "min_cert_level": 4},
    ]


def bundle_clean_queue(rng: random.Random) -> dict:
    d1, d2 = f"d-{rng.randint(100,999)}", f"d-{rng.randint(100,999)}"
    p1 = f"p-{rng.randint(10000,99999)}"
    p2 = f"p-{rng.randint(10000,99999)}"
    i1 = f"ins-{rng.randint(100,999)}"
    i2 = f"ins-{rng.randint(100,999)}"
    return {
        "scenario": "clean-queue",
        "planning_epoch_day": 18000,
        "permits": [
            {"permit_id": p1, "district_id": d1, "permit_type": "building-residential", "base_priority": 3, "requested_day": 18005, "deferred": False},
            {"permit_id": p2, "district_id": d2, "permit_type": "plumbing-major", "base_priority": 2, "requested_day": 18006, "deferred": False},
        ],
        "inspectors": [
            {"inspector_id": i1, "cert_level": 3, "districts": [d1, d2], "daily_cap": 2, "available_day": 18000},
            {"inspector_id": i2, "cert_level": 2, "districts": [d2], "daily_cap": 1, "available_day": 18000},
        ],
        "zoning_holds": [],
        "blackout_windows": [],
        "violations": [],
        "permit_routes": _routes(),
    }


def bundle_violation_priority(rng: random.Random) -> dict:
    d = f"d-{rng.randint(100,999)}"
    pa = f"p-{rng.randint(10000,99999)}"
    pb = f"p-{rng.randint(10000,99999)}"
    ins = f"ins-{rng.randint(100,999)}"
    return {
        "scenario": "violation-priority",
        "planning_epoch_day": 18000,
        "permits": [
            {"permit_id": pa, "district_id": d, "permit_type": "building-commercial", "base_priority": 2, "requested_day": 18010, "deferred": False},
            {"permit_id": pb, "district_id": d, "permit_type": "building-commercial", "base_priority": 2, "requested_day": 18010, "deferred": False},
        ],
        "inspectors": [{"inspector_id": ins, "cert_level": 4, "districts": [d], "daily_cap": 2, "available_day": 18000}],
        "zoning_holds": [],
        "blackout_windows": [],
        "violations": [
            {"permit_id": pa, "severity": 2, "days_ago": 5},
            {"permit_id": pb, "severity": 4, "days_ago": 2},
        ],
        "permit_routes": _routes(),
    }


def bundle_zoning_hold(rng: random.Random) -> dict:
    d = f"d-{rng.randint(100,999)}"
    p = f"p-{rng.randint(10000,99999)}"
    ins = f"ins-{rng.randint(100,999)}"
    return {
        "scenario": "zoning-hold-block",
        "planning_epoch_day": 18000,
        "permits": [{"permit_id": p, "district_id": d, "permit_type": "zoning-variance", "base_priority": 5, "requested_day": 18008, "deferred": False}],
        "inspectors": [{"inspector_id": ins, "cert_level": 5, "districts": [d], "daily_cap": 1, "available_day": 18000}],
        "zoning_holds": [{"district_id": d, "hold_rank": 3, "active": True, "reason_code": "floodplain"}],
        "blackout_windows": [],
        "violations": [],
        "permit_routes": _routes(),
    }


def bundle_blackout_edge(rng: random.Random) -> dict:
    d = f"d-{rng.randint(100,999)}"
    p = f"p-{rng.randint(10000,99999)}"
    ins = f"ins-{rng.randint(100,999)}"
    end = 18012
    return {
        "scenario": "blackout-inclusive-end",
        "planning_epoch_day": 18000,
        "permits": [{"permit_id": p, "district_id": d, "permit_type": "building-residential", "base_priority": 3, "requested_day": end, "deferred": False}],
        "inspectors": [{"inspector_id": ins, "cert_level": 3, "districts": [d], "daily_cap": 1, "available_day": 18000}],
        "zoning_holds": [],
        "blackout_windows": [{"district_id": d, "start_day": 18010, "end_day": end}],
        "violations": [],
        "permit_routes": _routes(),
    }


def bundle_cert_floor(rng: random.Random) -> dict:
    d = f"d-{rng.randint(100,999)}"
    p = f"p-{rng.randint(10000,99999)}"
    i_low = f"ins-{rng.randint(100,999)}"
    i_ok = f"ins-{rng.randint(100,999)}"
    return {
        "scenario": "cert-floor-edge",
        "planning_epoch_day": 18000,
        "permits": [{"permit_id": p, "district_id": d, "permit_type": "electrical-service", "base_priority": 4, "requested_day": 18007, "deferred": False}],
        "inspectors": [
            {"inspector_id": i_low, "cert_level": 3, "districts": [d], "daily_cap": 1, "available_day": 18000},
            {"inspector_id": i_ok, "cert_level": 3, "districts": [d], "daily_cap": 1, "available_day": 18000},
        ],
        "zoning_holds": [],
        "blackout_windows": [],
        "violations": [],
        "permit_routes": _routes(),
    }


def bundle_electrical_lane(rng: random.Random) -> dict:
    d = f"d-{rng.randint(100,999)}"
    p = f"p-{rng.randint(10000,99999)}"
    ins = f"ins-{rng.randint(100,999)}"
    return {
        "scenario": "electrical-lane-route",
        "planning_epoch_day": 18000,
        "permits": [{"permit_id": p, "district_id": d, "permit_type": "electrical-renewal", "base_priority": 3, "requested_day": 18009, "deferred": False}],
        "inspectors": [{"inspector_id": ins, "cert_level": 2, "districts": [d], "daily_cap": 1, "available_day": 18000}],
        "zoning_holds": [],
        "blackout_windows": [],
        "violations": [],
        "permit_routes": _routes(),
    }


def bundle_stable_tie(rng: random.Random) -> dict:
    d = f"d-{rng.randint(100,999)}"
    pa = f"p-{rng.randint(10000,89999)}"
    pb = f"p-{rng.randint(90000,99999)}"
    ins = f"ins-{rng.randint(100,999)}"
    return {
        "scenario": "stable-order-tie",
        "planning_epoch_day": 18000,
        "permits": [
            {"permit_id": pb, "district_id": d, "permit_type": "plumbing-major", "base_priority": 3, "requested_day": 18011, "deferred": False},
            {"permit_id": pa, "district_id": d, "permit_type": "plumbing-major", "base_priority": 3, "requested_day": 18011, "deferred": False},
        ],
        "inspectors": [{"inspector_id": ins, "cert_level": 3, "districts": [d], "daily_cap": 2, "available_day": 18000}],
        "zoning_holds": [],
        "blackout_windows": [],
        "violations": [],
        "permit_routes": _routes(),
    }


BUILDERS = [
    bundle_clean_queue,
    bundle_violation_priority,
    bundle_zoning_hold,
    bundle_blackout_edge,
    bundle_cert_floor,
    bundle_electrical_lane,
    bundle_stable_tie,
]


def write_bundle(name: str, data: dict) -> None:
    dest = ROOT / name
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "bundle.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for fn in BUILDERS:
        data = fn(_rng(fn.__name__))
        write_bundle(data["scenario"], data)
    repo_hidden = Path(__file__).resolve().parent.parent / "hidden" / "scenarios"
    repo_hidden.mkdir(parents=True, exist_ok=True)
    for fn in BUILDERS[:2]:
        data = fn(_rng("hidden-" + fn.__name__))
        data["scenario"] = "hidden-" + data["scenario"]
        dest = repo_hidden / data["scenario"]
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "bundle.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
