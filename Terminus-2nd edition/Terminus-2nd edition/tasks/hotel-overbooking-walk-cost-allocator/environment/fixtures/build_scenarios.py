#!/usr/bin/env python3
"""Build SQLite hotel scenarios with seeded randomized ids."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT
HIDDEN_ROOT = Path(os.environ.get("OVERBOOK_HIDDEN_ROOT", "")) if os.environ.get("OVERBOOK_HIDDEN_ROOT") else None


def seed_ids(seed: str, labels: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for label in labels:
        digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()
        out[label] = f"{label[:3]}-{digest[:8]}"
    return out


def write_db(path: Path, meta: dict, rows: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE scenario_meta (scenario TEXT, night_date TEXT, catalog_seed TEXT);
        CREATE TABLE room_types (room_type_id TEXT, name TEXT, rank INTEGER);
        CREATE TABLE rooms (room_id TEXT, room_type_id TEXT, status TEXT);
        CREATE TABLE reservations (reservation_id TEXT, guest_id TEXT, room_type_id TEXT, loyalty_tier TEXT, cancel_prob REAL, arrival_rank INTEGER);
        CREATE TABLE maintenance_windows (room_id TEXT, start_date TEXT, end_date TEXT);
        CREATE TABLE loyalty_policies (tier_name TEXT, protection_rank INTEGER);
        CREATE TABLE substitution_rules (from_type_id TEXT, to_type_id TEXT);
        CREATE TABLE walk_costs (from_type_id TEXT, to_type_id TEXT, cost_cents INTEGER);
        """
    )
    cur.execute(
        "INSERT INTO scenario_meta VALUES (?,?,?)",
        (meta["scenario"], meta["night_date"], meta["catalog_seed"]),
    )
    for rt in rows["room_types"]:
        cur.execute("INSERT INTO room_types VALUES (?,?,?)", (rt["room_type_id"], rt["name"], rt["rank"]))
    for r in rows["rooms"]:
        cur.execute("INSERT INTO rooms VALUES (?,?,?)", (r["room_id"], r["room_type_id"], r["status"]))
    for res in rows["reservations"]:
        cur.execute(
            "INSERT INTO reservations VALUES (?,?,?,?,?,?)",
            (
                res["reservation_id"],
                res["guest_id"],
                res["room_type_id"],
                res["loyalty_tier"],
                res["cancel_prob"],
                res["arrival_rank"],
            ),
        )
    for m in rows.get("maintenance", []):
        cur.execute("INSERT INTO maintenance_windows VALUES (?,?,?)", (m["room_id"], m["start_date"], m["end_date"]))
    for pol in rows["loyalty"]:
        cur.execute("INSERT INTO loyalty_policies VALUES (?,?)", (pol["tier_name"], pol["protection_rank"]))
    for rule in rows.get("substitutions", []):
        cur.execute("INSERT INTO substitution_rules VALUES (?,?)", (rule["from_type_id"], rule["to_type_id"]))
    for wc in rows.get("walk_costs", []):
        cur.execute("INSERT INTO walk_costs VALUES (?,?,?)", (wc["from_type_id"], wc["to_type_id"], wc["cost_cents"]))
    conn.commit()
    conn.close()


def base_types(seed: str) -> dict:
    ids = seed_ids(seed, ["std", "dlx", "ste"])
    return {
        "std": {"room_type_id": ids["std"], "name": "standard", "rank": 1},
        "dlx": {"room_type_id": ids["dlx"], "name": "deluxe", "rank": 2},
        "ste": {"room_type_id": ids["ste"], "name": "suite", "rank": 3},
    }


def default_loyalty() -> list[dict]:
    return [
        {"tier_name": "platinum", "protection_rank": 1},
        {"tier_name": "gold", "protection_rank": 5},
        {"tier_name": "standard", "protection_rank": 20},
    ]


def default_walk_costs(types: dict) -> list[dict]:
    std, dlx, ste = types["std"]["room_type_id"], types["dlx"]["room_type_id"], types["ste"]["room_type_id"]
    return [
        {"from_type_id": std, "to_type_id": dlx, "cost_cents": 4500},
        {"from_type_id": std, "to_type_id": ste, "cost_cents": 9000},
        {"from_type_id": dlx, "to_type_id": ste, "cost_cents": 5000},
    ]


def default_subst(types: dict) -> list[dict]:
    std, dlx, ste = types["std"]["room_type_id"], types["dlx"]["room_type_id"], types["ste"]["room_type_id"]
    return [
        {"from_type_id": std, "to_type_id": dlx},
        {"from_type_id": std, "to_type_id": ste},
        {"from_type_id": dlx, "to_type_id": ste},
    ]


def scenario_clean(seed: str) -> dict:
    types = base_types(seed)
    ids = seed_ids(seed, ["rm-1", "rm-2", "g-1", "g-2", "res-1", "res-2"])
    std = types["std"]["room_type_id"]
    return {
        "room_types": list(types.values()),
        "rooms": [
            {"room_id": ids["rm-1"], "room_type_id": std, "status": "available"},
            {"room_id": ids["rm-2"], "room_type_id": std, "status": "available"},
        ],
        "loyalty": default_loyalty(),
        "substitutions": default_subst(types),
        "walk_costs": default_walk_costs(types),
        "reservations": [
            {
                "reservation_id": ids["res-1"],
                "guest_id": ids["g-1"],
                "room_type_id": std,
                "loyalty_tier": "standard",
                "cancel_prob": 0.05,
                "arrival_rank": 1,
            },
            {
                "reservation_id": ids["res-2"],
                "guest_id": ids["g-2"],
                "room_type_id": std,
                "loyalty_tier": "gold",
                "cancel_prob": 0.10,
                "arrival_rank": 2,
            },
        ],
        "maintenance": [],
    }


def scenario_overbook(seed: str) -> dict:
    base = scenario_clean(seed)
    ids = seed_ids(seed, ["g-3", "res-3"])
    std = base["room_types"][0]["room_type_id"]
    base["reservations"].append(
        {
            "reservation_id": ids["res-3"],
            "guest_id": ids["g-3"],
            "room_type_id": std,
            "loyalty_tier": "standard",
            "cancel_prob": 0.80,
            "arrival_rank": 3,
        }
    )
    return base


def scenario_maintenance(seed: str) -> dict:
    base = scenario_clean(seed)
    base["rooms"] = base["rooms"][:1]
    base["maintenance"] = [
        {"room_id": base["rooms"][0]["room_id"], "start_date": "2026-04-01", "end_date": "2026-04-10"},
    ]
    return base


def scenario_loyalty(seed: str) -> dict:
    base = scenario_overbook(seed)
    base["reservations"][0]["loyalty_tier"] = "platinum"
    base["reservations"][0]["cancel_prob"] = 0.02
    base["reservations"][2]["cancel_prob"] = 0.90
    return base


def scenario_substitution(seed: str) -> dict:
    base = scenario_clean(seed)
    types = {t["name"]: t for t in base["room_types"]}
    ids = seed_ids(seed, ["rm-d", "res-d", "g-d"])
    base["rooms"] = [{"room_id": ids["rm-d"], "room_type_id": types["deluxe"]["room_type_id"], "status": "available"}]
    base["reservations"] = [
        {
            "reservation_id": ids["res-d"],
            "guest_id": ids["g-d"],
            "room_type_id": types["standard"]["room_type_id"],
            "loyalty_tier": "gold",
            "cancel_prob": 0.05,
            "arrival_rank": 1,
        }
    ]
    return base


def scenario_demand(seed: str) -> dict:
    base = scenario_overbook(seed)
    base["reservations"][1]["cancel_prob"] = 0.05
    base["reservations"][2]["cancel_prob"] = 0.95
    base["reservations"][2]["arrival_rank"] = 2
    base["reservations"][1]["arrival_rank"] = 3
    return base


def scenario_walk_tie(seed: str) -> dict:
    base = scenario_overbook(seed)
    types = {t["name"]: t for t in base["room_types"]}
    std = types["standard"]["room_type_id"]
    dlx = types["deluxe"]["room_type_id"]
    ste = types["suite"]["room_type_id"]
    base["rooms"] = []
    base["walk_costs"] = [
        {"from_type_id": std, "to_type_id": dlx, "cost_cents": 3000},
        {"from_type_id": std, "to_type_id": ste, "cost_cents": 3000},
    ]
    return base


def scenario_stable_rerun(seed: str) -> dict:
    return scenario_clean(seed)


def scenario_maint_boundary(seed: str) -> dict:
    base = scenario_clean(seed)
    base["maintenance"] = [
        {"room_id": base["rooms"][0]["room_id"], "start_date": "2026-04-01", "end_date": "2026-04-05"},
    ]
    base["meta_date"] = "2026-04-05"
    return base


def scenario_walk_hidden(seed: str) -> dict:
    base = scenario_overbook(seed)
    types = {t["name"]: t for t in base["room_types"]}
    std = types["standard"]["room_type_id"]
    dlx = types["deluxe"]["room_type_id"]
    ste = types["suite"]["room_type_id"]
    base["rooms"] = []
    base["walk_costs"] = [
        {"from_type_id": std, "to_type_id": ste, "cost_cents": 2000},
        {"from_type_id": std, "to_type_id": dlx, "cost_cents": 2500},
    ]
    base["reservations"][2]["cancel_prob"] = 0.99
    return base


BUILDERS = {
    "clean-night": scenario_clean,
    "overbook-single": scenario_overbook,
    "maintenance-block": scenario_maintenance,
    "loyalty-shield": scenario_loyalty,
    "substitution-upgrade": scenario_substitution,
    "demand-ranking": scenario_demand,
    "walk-cost-tie": scenario_walk_tie,
    "stable-rerun": scenario_stable_rerun,
    "maintenance-boundary-trap": scenario_maint_boundary,
    "walk-cost-hidden-trap": scenario_walk_hidden,
}


def emit(name: str, out_root: Path) -> None:
    seed = hashlib.sha256(name.encode()).hexdigest()[:16]
    rows = BUILDERS[name](seed)
    night_date = rows.pop("meta_date", "2026-04-05")
    meta = {"scenario": name, "night_date": night_date, "catalog_seed": seed}
    dest = out_root / "scenarios" / name
    write_db(dest / "hotel.db", meta, rows)
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


BUNDLED = (
    "clean-night",
    "overbook-single",
    "maintenance-block",
    "loyalty-shield",
    "substitution-upgrade",
    "demand-ranking",
    "walk-cost-tie",
    "stable-rerun",
)
HIDDEN = (
    "maintenance-boundary-trap",
    "walk-cost-hidden-trap",
)


def main() -> None:
    targets = [DEFAULT_OUT]
    if HIDDEN_ROOT is not None and HIDDEN_ROOT.is_dir():
        targets.append(HIDDEN_ROOT)
    for out_root in targets:
        names = list(BUNDLED) if out_root == DEFAULT_OUT else list(HIDDEN)
        for name in names:
            emit(name, out_root)


if __name__ == "__main__":
    main()
