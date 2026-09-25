#!/usr/bin/env python3
"""Build bundled and hidden airclos closure-lab campaign fixtures."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN_ROOT = Path(os.environ.get("AIRCLOS_HIDDEN_ROOT", ""))


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, separators=(",", ":")) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fixture_digest(payload: object) -> str:
    """Stable sha256 over canonical JSON for fixture inventory tags."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def rect_sector(sid: str, x0: float, y0: float, x1: float, y1: float) -> dict:
    return {
        "sector_id": sid,
        "polygon": [
            {"x": x0, "y": y0},
            {"x": x1, "y": y0},
            {"x": x1, "y": y1},
            {"x": x0, "y": y1},
        ],
    }


def l_shape_sector(sid: str) -> dict:
    return {
        "sector_id": sid,
        "polygon": [
            {"x": 0, "y": 0},
            {"x": 4, "y": 0},
            {"x": 4, "y": 2},
            {"x": 2, "y": 2},
            {"x": 2, "y": 4},
            {"x": 0, "y": 4},
        ],
    }


SCENARIOS: dict[str, dict] = {
    "amend-latest-wins": {
        "policy": {"eval_minute": 150},
        "notams": [
            {
                "notam_id": "A001/26",
                "series_id": "SER-A",
                "amendment": 1,
                "start_minute": 100,
                "end_minute": 200,
                "kind": "sector",
                "sector_id": "SEC-EAST",
                "polygon": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}, {"x": 0, "y": 10}],
                "impact_code": "sector_closed",
            },
            {
                "notam_id": "A001/26A2",
                "series_id": "SER-A",
                "amendment": 2,
                "start_minute": 120,
                "end_minute": 220,
                "kind": "sector",
                "sector_id": "SEC-EAST",
                "polygon": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}, {"x": 0, "y": 10}],
                "impact_code": "sector_closed",
            },
        ],
        "sectors": [rect_sector("SEC-EAST", 0, 0, 10, 10)],
        "flights": [{"flight_id": "F1", "route_fixes": ["FIX-A"]}],
        "fix_points": [{"fix_id": "FIX-A", "x": 5, "y": 5}],
        "airways": [],
    },
    "midnight-window-active": {
        "policy": {"eval_minute": 30},
        "notams": [
            {
                "notam_id": "B002/26",
                "series_id": "SER-B",
                "amendment": 1,
                "start_minute": 1380,
                "end_minute": 90,
                "kind": "route",
                "route_fix": "NITE",
                "impact_code": "route_closed",
            }
        ],
        "sectors": [rect_sector("SEC-N", 0, 0, 20, 20)],
        "flights": [{"flight_id": "N1", "route_fixes": ["DEP", "NITE", "ARR"]}],
        "fix_points": [
            {"fix_id": "DEP", "x": 1, "y": 1},
            {"fix_id": "NITE", "x": 5, "y": 5},
            {"fix_id": "ARR", "x": 9, "y": 9},
        ],
        "airways": [],
    },
    "sector-fix-inside": {
        "policy": {"eval_minute": 400},
        "notams": [
            {
                "notam_id": "C003/26",
                "series_id": "SER-C",
                "amendment": 1,
                "start_minute": 300,
                "end_minute": 500,
                "kind": "sector",
                "sector_id": "SEC-L",
                "polygon": [
                    {"x": 0, "y": 0},
                    {"x": 4, "y": 0},
                    {"x": 4, "y": 2},
                    {"x": 2, "y": 2},
                    {"x": 2, "y": 4},
                    {"x": 0, "y": 4},
                ],
                "impact_code": "sector_closed",
            }
        ],
        "sectors": [l_shape_sector("SEC-L")],
        "flights": [{"flight_id": "L1", "route_fixes": ["INNER"]}],
        "fix_points": [{"fix_id": "INNER", "x": 1, "y": 3}],
        "airways": [],
    },
    "runway-normalize-match": {
        "policy": {"eval_minute": 800},
        "notams": [
            {
                "notam_id": "D004/26",
                "series_id": "SER-D",
                "amendment": 1,
                "start_minute": 700,
                "end_minute": 900,
                "kind": "runway",
                "airport": "KZZZ",
                "runway": "09L",
                "impact_code": "runway_closed",
            }
        ],
        "sectors": [rect_sector("SEC-R", 0, 0, 5, 5)],
        "flights": [
            {
                "flight_id": "R1",
                "route_fixes": ["DEP"],
                "airport": "KZZZ",
                "runways": ["9l"],
            }
        ],
        "fix_points": [{"fix_id": "DEP", "x": 1, "y": 1}],
        "airways": [],
    },
    "airway-catalog-expand": {
        "policy": {"eval_minute": 600},
        "notams": [
            {
                "notam_id": "E005/26",
                "series_id": "SER-E",
                "amendment": 1,
                "start_minute": 500,
                "end_minute": 700,
                "kind": "route",
                "route_fix": "MID",
                "impact_code": "route_restricted",
            }
        ],
        "sectors": [rect_sector("SEC-W", 0, 0, 30, 30)],
        "flights": [{"flight_id": "W1", "route_fixes": ["DEP", "AWY-7", "ARR"]}],
        "fix_points": [
            {"fix_id": "DEP", "x": 2, "y": 2},
            {"fix_id": "MID", "x": 15, "y": 15},
            {"fix_id": "ARR", "x": 28, "y": 28},
        ],
        "airways": [{"airway_id": "AWY-7", "fixes": ["DEP", "MID", "ARR"]}],
    },
    "inactive-window-skip": {
        "policy": {"eval_minute": 700},
        "notams": [
            {
                "notam_id": "F006/26",
                "series_id": "SER-F",
                "amendment": 1,
                "start_minute": 500,
                "end_minute": 600,
                "kind": "sector",
                "sector_id": "SEC-IDLE",
                "polygon": [{"x": 0, "y": 0}, {"x": 5, "y": 0}, {"x": 5, "y": 5}, {"x": 0, "y": 5}],
                "impact_code": "sector_closed",
            }
        ],
        "sectors": [rect_sector("SEC-IDLE", 0, 0, 5, 5)],
        "flights": [{"flight_id": "I1", "route_fixes": ["P1"]}],
        "fix_points": [{"fix_id": "P1", "x": 2, "y": 2}],
        "airways": [],
    },
    "multi-flight-mixed": {
        "policy": {"eval_minute": 950},
        "notams": [
            {
                "notam_id": "G007/26",
                "series_id": "SER-G1",
                "amendment": 1,
                "start_minute": 900,
                "end_minute": 1000,
                "kind": "runway",
                "airport": "KABC",
                "runway": "27R",
                "impact_code": "runway_closed",
            },
            {
                "notam_id": "G008/26",
                "series_id": "SER-G2",
                "amendment": 1,
                "start_minute": 900,
                "end_minute": 1000,
                "kind": "sector",
                "sector_id": "SEC-MIX",
                "polygon": [{"x": 10, "y": 10}, {"x": 20, "y": 10}, {"x": 20, "y": 20}, {"x": 10, "y": 20}],
                "impact_code": "sector_closed",
            },
        ],
        "sectors": [rect_sector("SEC-MIX", 10, 10, 20, 20)],
        "flights": [
            {"flight_id": "M1", "route_fixes": ["X1"], "airport": "KABC", "runways": ["27R"]},
            {"flight_id": "M2", "route_fixes": ["X2"]},
        ],
        "fix_points": [
            {"fix_id": "X1", "x": 1, "y": 1},
            {"fix_id": "X2", "x": 15, "y": 15},
        ],
        "airways": [],
    },
    "stable-repeat-report": {
        "policy": {"eval_minute": 1100},
        "notams": [
            {
                "notam_id": "H009/26",
                "series_id": "SER-H",
                "amendment": 1,
                "start_minute": 1000,
                "end_minute": 1200,
                "kind": "route",
                "route_fix": "STAB",
                "impact_code": "route_closed",
            }
        ],
        "sectors": [rect_sector("SEC-S", 0, 0, 8, 8)],
        "flights": [{"flight_id": "S1", "route_fixes": ["A0", "STAB", "B0"]}],
        "fix_points": [
            {"fix_id": "A0", "x": 1, "y": 1},
            {"fix_id": "STAB", "x": 4, "y": 4},
            {"fix_id": "B0", "x": 7, "y": 7},
        ],
        "airways": [],
    },
}

HIDDEN_SCENARIOS: dict[str, dict] = {
    "midnight-edge-eq": {
        "policy": {"eval_minute": 90},
        "notams": [
            {
                "notam_id": "T101/26",
                "series_id": "SER-T1",
                "amendment": 1,
                "start_minute": 1380,
                "end_minute": 90,
                "kind": "route",
                "route_fix": "EDGE",
                "impact_code": "route_closed",
            }
        ],
        "sectors": [rect_sector("SEC-T", 0, 0, 12, 12)],
        "flights": [{"flight_id": "T1", "route_fixes": ["EDGE"]}],
        "fix_points": [{"fix_id": "EDGE", "x": 6, "y": 6}],
        "airways": [],
    },
    "amend-zero-series-trap": {
        "policy": {"eval_minute": 250},
        "notams": [
            {
                "notam_id": "T201/26",
                "series_id": "SER-T2",
                "amendment": 0,
                "start_minute": 200,
                "end_minute": 300,
                "kind": "route",
                "route_fix": "OLDX",
                "impact_code": "route_closed",
            },
            {
                "notam_id": "T202/26",
                "series_id": "SER-T2",
                "amendment": 3,
                "start_minute": 200,
                "end_minute": 300,
                "kind": "route",
                "route_fix": "NEWX",
                "impact_code": "route_closed",
            },
        ],
        "sectors": [rect_sector("SEC-T2", 0, 0, 6, 6)],
        "flights": [{"flight_id": "T2A", "route_fixes": ["NEWX"]}, {"flight_id": "T2B", "route_fixes": ["OLDX"]}],
        "fix_points": [
            {"fix_id": "NEWX", "x": 2, "y": 2},
            {"fix_id": "OLDX", "x": 4, "y": 4},
        ],
        "airways": [],
    },
}


def materialize(base: Path, scenarios: dict[str, dict]) -> None:
    inventory: dict[str, str] = {}
    for name, spec in scenarios.items():
        dest = base / "scenarios" / name
        write_json(dest / "policy.json", spec["policy"])
        write_jsonl(dest / "notams.jsonl", spec["notams"])
        write_json(dest / "sectors.json", spec["sectors"])
        write_jsonl(dest / "flights.jsonl", spec["flights"])
        write_json(dest / "fix_points.json", spec["fix_points"])
        write_json(dest / "airways.json", spec["airways"])
        inventory[name] = fixture_digest(spec)
    write_json(base / "fixture-inventory.json", inventory)


def main() -> None:
    materialize(ROOT, SCENARIOS)
    if HIDDEN_ROOT:
        materialize(HIDDEN_ROOT, HIDDEN_SCENARIOS)
        print(f"hidden fixtures written under {HIDDEN_ROOT}")
    print("airclos closure-lab fixtures ready")


if __name__ == "__main__":
    main()
