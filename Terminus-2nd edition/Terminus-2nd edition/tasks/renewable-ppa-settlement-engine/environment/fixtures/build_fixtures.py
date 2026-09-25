#!/usr/bin/env python3
"""Fixture catalog builder for ppareconctl PPA settlement scenarios."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

BUNDLED = (
    "clean-interval",
    "curtailment-skip",
    "strike-floor",
    "holiday-trim",
    "multi-meter",
    "republish-stable",
)

HIDDEN = (
    "curtail-end-boundary-trap",
    "market-exact-interval-trap",
)


def _body(scenario: str) -> dict:
    if scenario == "clean-interval":
        return {
            "scenario_id": scenario,
            "ppa_id": "PPA-SOLAR-01",
            "period_start": "2026-01-01",
            "period_end": "2026-01-07",
            "strike_price_cents": 4500,
            "interval_minutes": 15,
            "holidays": [],
            "meters": [
                {
                    "meter_id": "M-SOL-A",
                    "readings": [{"ts_utc": "2026-01-02T12:07:33Z", "mwh": 1.5}],
                }
            ],
            "curtailments": [],
            "market_prices": [
                {"interval_start_utc": "2026-01-02T12:00:00Z", "price_cents": 3200}
            ],
        }
    if scenario == "curtailment-skip":
        return {
            "scenario_id": scenario,
            "ppa_id": "PPA-WIND-02",
            "period_start": "2026-01-01",
            "period_end": "2026-01-07",
            "strike_price_cents": 4200,
            "interval_minutes": 15,
            "holidays": [],
            "meters": [
                {
                    "meter_id": "M-WIN-B",
                    "readings": [{"ts_utc": "2026-01-03T12:04:00Z", "mwh": 2.0}],
                }
            ],
            "curtailments": [
                {"start_utc": "2026-01-03T12:00:00Z", "end_utc": "2026-01-03T13:00:00Z"}
            ],
            "market_prices": [
                {"interval_start_utc": "2026-01-03T12:00:00Z", "price_cents": 3800}
            ],
        }
    if scenario == "strike-floor":
        return {
            "scenario_id": scenario,
            "ppa_id": "PPA-HYDRO-03",
            "period_start": "2026-01-01",
            "period_end": "2026-01-07",
            "strike_price_cents": 4500,
            "interval_minutes": 15,
            "holidays": [],
            "meters": [
                {
                    "meter_id": "M-HYD-C",
                    "readings": [{"ts_utc": "2026-01-04T08:22:10Z", "mwh": 1.0}],
                }
            ],
            "curtailments": [],
            "market_prices": [
                {"interval_start_utc": "2026-01-04T08:15:00Z", "price_cents": 5200}
            ],
        }
    if scenario == "holiday-trim":
        return {
            "scenario_id": scenario,
            "ppa_id": "PPA-SOLAR-04",
            "period_start": "2026-01-01",
            "period_end": "2026-01-07",
            "strike_price_cents": 4100,
            "interval_minutes": 15,
            "holidays": ["2026-01-01", "2026-01-20"],
            "meters": [
                {
                    "meter_id": "M-SOL-D",
                    "readings": [{"ts_utc": "2026-01-02T10:00:00Z", "mwh": 0.5}],
                }
            ],
            "curtailments": [],
            "market_prices": [
                {"interval_start_utc": "2026-01-02T10:00:00Z", "price_cents": 3000}
            ],
        }
    if scenario == "multi-meter":
        return {
            "scenario_id": scenario,
            "ppa_id": "PPA-MIX-05",
            "period_start": "2026-01-01",
            "period_end": "2026-01-07",
            "strike_price_cents": 4400,
            "interval_minutes": 15,
            "holidays": [],
            "meters": [
                {
                    "meter_id": "M-A",
                    "readings": [{"ts_utc": "2026-01-05T06:10:00Z", "mwh": 1.2}],
                },
                {
                    "meter_id": "M-B",
                    "readings": [{"ts_utc": "2026-01-05T06:12:00Z", "mwh": 0.8}],
                },
            ],
            "curtailments": [],
            "market_prices": [
                {"interval_start_utc": "2026-01-05T06:00:00Z", "price_cents": 3600}
            ],
        }
    if scenario == "republish-stable":
        return {
            "scenario_id": scenario,
            "ppa_id": "PPA-REP-06",
            "period_start": "2026-01-01",
            "period_end": "2026-01-03",
            "strike_price_cents": 4300,
            "interval_minutes": 15,
            "holidays": [],
            "meters": [
                {
                    "meter_id": "M-REP",
                    "readings": [{"ts_utc": "2026-01-02T14:30:00Z", "mwh": 2.5}],
                }
            ],
            "curtailments": [],
            "market_prices": [
                {"interval_start_utc": "2026-01-02T14:30:00Z", "price_cents": 4000}
            ],
        }
    if scenario == "curtail-end-boundary-trap":
        return {
            "scenario_id": scenario,
            "ppa_id": "PPA-TRAP-07",
            "period_start": "2026-01-01",
            "period_end": "2026-01-07",
            "strike_price_cents": 4600,
            "interval_minutes": 15,
            "holidays": [],
            "meters": [
                {
                    "meter_id": "M-TRAP-A",
                    "readings": [{"ts_utc": "2026-01-06T15:15:00Z", "mwh": 1.1}],
                }
            ],
            "curtailments": [
                {"start_utc": "2026-01-06T15:00:00Z", "end_utc": "2026-01-06T15:15:00Z"}
            ],
            "market_prices": [
                {"interval_start_utc": "2026-01-06T15:15:00Z", "price_cents": 3500}
            ],
        }
    if scenario == "market-exact-interval-trap":
        return {
            "scenario_id": scenario,
            "ppa_id": "PPA-TRAP-08",
            "period_start": "2026-01-01",
            "period_end": "2026-01-07",
            "strike_price_cents": 4700,
            "interval_minutes": 15,
            "holidays": [],
            "meters": [
                {
                    "meter_id": "M-TRAP-B",
                    "readings": [{"ts_utc": "2026-01-07T09:30:00Z", "mwh": 1.3}],
                }
            ],
            "curtailments": [],
            "market_prices": [
                {"interval_start_utc": "2026-01-07T09:30:00Z", "price_cents": 5100}
            ],
        }
    raise ValueError(f"unknown scenario {scenario}")


def _write(root: Path, scenario: str) -> None:
    out = root / "scenarios" / f"{scenario}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_body(scenario), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _catalog_digest(names: tuple[str, ...]) -> str:
    joined = ",".join(sorted(names))
    return hashlib.sha256(joined.encode()).hexdigest()[: int(math.ceil(8))]


def main() -> None:
    hidden_root = os.environ.get("PPA_HIDDEN_ROOT")
    if hidden_root:
        base = Path(hidden_root)
        for name in HIDDEN:
            _write(base, name)
        return
    base = Path("/app/fixtures")
    if not Path("/app").exists():
        base = Path(__file__).resolve().parent
    for name in BUNDLED:
        _write(base, name)
    catalog_path = base / "catalog-digest.txt"
    catalog_path.write_text(_catalog_digest(BUNDLED) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
