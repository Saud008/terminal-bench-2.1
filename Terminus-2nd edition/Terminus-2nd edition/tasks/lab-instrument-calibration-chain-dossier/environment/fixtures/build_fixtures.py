#!/usr/bin/env python3
"""Generate randomized calibration run packs for caldoss verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def _inst_id(rng: random.Random) -> str:
    return f"INST-{rng.randint(10000, 99999)}"


def _cert_id(rng: random.Random) -> str:
    return f"CERT-{hashlib.sha256(str(rng.random()).encode()).hexdigest()[:10].upper()}"


def _tech_id(rng: random.Random) -> str:
    return f"TECH-{rng.randint(1000, 9999)}"


def _base_pack(
    rng: random.Random,
    *,
    as_of: str,
    expires: str,
    readings: list[dict],
    chain: list[dict],
    scope: list[str] | None,
    budget: list[dict],
    instrument: str | None = None,
) -> dict:
    instrument_id = instrument or _inst_id(rng)
    gate_operator = scope if scope is not None else [instrument_id]
    return {
        "run_id": f"RUN-{rng.randint(100000, 999999)}",
        "as_of_date": as_of,
        "instrument_id": instrument_id,
        "readings": readings,
        "certificate": {
            "cert_id": _cert_id(rng),
            "issued": "2025-01-01",
            "expires": expires,
            "issuer": "MetroLab",
        },
        "standard_chain": chain,
        "technician": {
            "tech_id": _tech_id(rng),
            "scope_instruments": gate_operator,
            "qual_expires": "2027-12-31",
        },
        "uncertainty_budget": budget,
    }


def build_catalog(seed: int) -> dict[str, dict]:
    rng = random.Random(seed)
    inst_a = _inst_id(rng)
    inst_b = _inst_id(rng)
    root = f"NIST-{rng.randint(100, 999)}"
    mid = f"LAB-{rng.randint(100, 999)}"
    leaf = f"WRK-{rng.randint(100, 999)}"
    chain_deep = [
        {"std_id": root, "parent_std": None},
        {"std_id": mid, "parent_std": root},
        {"std_id": leaf, "parent_std": mid},
    ]
    chain_short = [
        {"std_id": root, "parent_std": None},
        {"std_id": leaf, "parent_std": root},
    ]
    budget_rss = [
        {"component": "repeatability", "value": 0.012, "degrees_freedom": 9},
        {"component": "drift", "value": 0.008, "degrees_freedom": 5},
        {"component": "resolution", "value": 0.005, "degrees_freedom": 50},
    ]
    return {
        "dual-channel-basic": _base_pack(
            rng,
            as_of="2026-03-15",
            expires="2026-12-31",
            instrument=inst_a,
            readings=[
                {
                    "channel": "pH",
                    "value": 7.02,
                    "unit": "pH",
                    "nominal": 7.0,
                    "tol_plus": 0.05,
                    "tol_minus": 0.03,
                },
                {
                    "channel": "tempC",
                    "value": 25.1,
                    "unit": "C",
                    "nominal": 25.0,
                    "tol_plus": 0.2,
                    "tol_minus": 0.15,
                },
            ],
            chain=chain_short,
            scope=None,
            budget=[{"component": "repeatability", "value": 0.01, "degrees_freedom": 9}],
        ),
        "cert-expired-edge": _base_pack(
            rng,
            as_of="2026-06-01",
            expires="2026-06-01",
            instrument=inst_b,
            readings=[
                {
                    "channel": "cond",
                    "value": 1.01,
                    "unit": "mS",
                    "nominal": 1.0,
                    "tol_plus": 0.05,
                    "tol_minus": 0.04,
                }
            ],
            chain=chain_short,
            scope=None,
            budget=[{"component": "repeatability", "value": 0.02, "degrees_freedom": 8}],
        ),
        "asymmetric-oot": _base_pack(
            rng,
            as_of="2026-04-10",
            expires="2027-01-01",
            readings=[
                {
                    "channel": "volt",
                    "value": 5.12,
                    "unit": "V",
                    "nominal": 5.0,
                    "tol_plus": 0.05,
                    "tol_minus": 0.2,
                }
            ],
            chain=chain_short,
            scope=None,
            budget=[{"component": "repeatability", "value": 0.015, "degrees_freedom": 6}],
        ),
        "trace-chain-deep": _base_pack(
            rng,
            as_of="2026-02-20",
            expires="2026-08-01",
            readings=[
                {
                    "channel": "mass",
                    "value": 100.0,
                    "unit": "g",
                    "nominal": 100.0,
                    "tol_plus": 0.1,
                    "tol_minus": 0.1,
                }
            ],
            chain=chain_deep,
            scope=None,
            budget=[{"component": "repeatability", "value": 0.003, "degrees_freedom": 12}],
        ),
        "tech-scope-miss": _base_pack(
            rng,
            as_of="2026-05-01",
            expires="2027-05-01",
            readings=[
                {
                    "channel": "flow",
                    "value": 10.0,
                    "unit": "L/min",
                    "nominal": 10.0,
                    "tol_plus": 0.5,
                    "tol_minus": 0.5,
                }
            ],
            chain=chain_short,
            scope=["INST-OTHER-99999"],
            budget=[{"component": "repeatability", "value": 0.02, "degrees_freedom": 4}],
        ),
        "rss-budget": _base_pack(
            rng,
            as_of="2026-07-01",
            expires="2027-07-01",
            readings=[
                {
                    "channel": "press",
                    "value": 101.3,
                    "unit": "kPa",
                    "nominal": 101.0,
                    "tol_plus": 0.5,
                    "tol_minus": 0.4,
                }
            ],
            chain=chain_short,
            scope=None,
            budget=budget_rss,
        ),
        "severity-ladder": _base_pack(
            rng,
            as_of="2026-08-15",
            expires="2026-01-01",
            readings=[
                {
                    "channel": "a",
                    "value": 2.0,
                    "unit": "u",
                    "nominal": 1.0,
                    "tol_plus": 0.2,
                    "tol_minus": 0.2,
                },
                {
                    "channel": "b",
                    "value": 0.5,
                    "unit": "u",
                    "nominal": 1.0,
                    "tol_plus": 0.2,
                    "tol_minus": 0.2,
                },
            ],
            chain=chain_short,
            scope=["INST-OTHER-99999"],
            budget=[{"component": "repeatability", "value": 0.04, "degrees_freedom": 3}],
        ),
        "generation-advance": _base_pack(
            rng,
            as_of="2026-09-01",
            expires="2027-09-01",
            readings=[
                {
                    "channel": "rpm",
                    "value": 3000.0,
                    "unit": "rpm",
                    "nominal": 3000.0,
                    "tol_plus": 50.0,
                    "tol_minus": 50.0,
                }
            ],
            chain=chain_short,
            scope=None,
            budget=[{"component": "repeatability", "value": 0.01, "degrees_freedom": 10}],
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    catalog = build_catalog(args.seed)
    registry = {
        "seed": args.seed,
        "packs": sorted(catalog.keys()),
        "batch_pool": ["BATCH-A", "BATCH-B"],
    }
    for name, body in catalog.items():
        (args.out_dir / f"{name}.json").write_text(
            json.dumps(body, indent=2) + "\n", encoding="utf-8"
        )
    (args.out_dir.parent / "run_registry.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
