"""Independent hotel finance reference simulator for ingest snapshot and export atlas phases."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def night_date(meta: dict) -> str:
    override = os.environ.get("TB3_NIGHT_DATE")
    return override or meta["night_date"]


def room_blocked(room_id: str, on_date: str, rows: list[sqlite3.Row]) -> bool:
    for row in rows:
        if row["room_id"] != room_id:
            continue
        if on_date >= row["start_date"] and on_date <= row["end_date"]:
            return True
    return False


def capacity_fingerprint(db_path: Path, meta: dict) -> str:
    conn = _connect(db_path)
    rooms = conn.execute("SELECT room_id, room_type_id FROM rooms ORDER BY room_id").fetchall()
    maint = conn.execute(
        "SELECT room_id, start_date, end_date FROM maintenance_windows ORDER BY room_id, start_date"
    ).fetchall()
    room_parts = [f"{r['room_id']}:{r['room_type_id']}" for r in rooms]
    maint_parts = [f"{m['room_id']}:{m['start_date']}:{m['end_date']}" for m in maint]
    payload = "|".join(room_parts) + "|" + meta["catalog_seed"] + "|" + "|".join(maint_parts)
    return hashlib.sha256(payload.encode()).hexdigest()


def protection_rank(tier: str, policies: dict[str, int]) -> int:
    return policies.get(tier, 50)


def demand_score(res: sqlite3.Row, policies: dict[str, int]) -> float:
    base = float(1000 - int(res["arrival_rank"])) * (1.0 - float(res["cancel_prob"]))
    shield = float(protection_rank(res["loyalty_tier"], policies))
    return base + shield * 0.01


def allowed_upgrade(from_type: str, to_type: str, ranks: dict[str, int], rules: set[tuple[str, str]]) -> bool:
    if (from_type, to_type) not in rules:
        return False
    return ranks[to_type] > ranks[from_type]


def pick_walk(from_type: str, ranks: dict[str, int], rules: set[tuple[str, str]], costs: list[sqlite3.Row]):
    choices = []
    for wc in costs:
        if wc["from_type_id"] != from_type:
            continue
        if not allowed_upgrade(from_type, wc["to_type_id"], ranks, rules):
            continue
        choices.append((int(wc["cost_cents"]), wc["to_type_id"]))
    if not choices:
        return None
    choices.sort(key=lambda t: (t[0], t[1]))
    return choices[0][1], choices[0][0]


def simulate_capacity_snapshot(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "hotel.db"
    meta = json.loads((fixture_root / "scenarios" / scenario / "meta.json").read_text(encoding="utf-8"))
    conn = _connect(db_path)
    room_count = conn.execute("SELECT COUNT(*) AS c FROM rooms").fetchone()["c"]
    maint_count = conn.execute("SELECT COUNT(*) AS c FROM maintenance_windows").fetchone()["c"]
    digest = capacity_fingerprint(db_path, meta)
    return {
        "scenario": scenario,
        "engine": "overbookctl",
        "capacity_fingerprint": digest,
        "room_count": room_count,
        "maintenance_count": maint_count,
    }


def simulate_displacement_atlas(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "hotel.db"
    meta_path = fixture_root / "scenarios" / scenario / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    on_date = night_date(meta)
    conn = _connect(db_path)
    ranks = {r["room_type_id"]: int(r["rank"]) for r in conn.execute("SELECT * FROM room_types")}
    policies = {
        r["tier_name"]: int(r["protection_rank"])
        for r in conn.execute("SELECT * FROM loyalty_policies")
    }
    rules = {
        (r["from_type_id"], r["to_type_id"])
        for r in conn.execute("SELECT * FROM substitution_rules")
    }
    costs = conn.execute("SELECT * FROM walk_costs").fetchall()
    maint = conn.execute("SELECT * FROM maintenance_windows").fetchall()
    rooms = [dict(r) for r in conn.execute("SELECT * FROM rooms ORDER BY room_id")]
    reservations = conn.execute("SELECT * FROM reservations").fetchall()
    scored = []
    for res in reservations:
        scored.append((demand_score(res, policies), int(res["arrival_rank"]), res["reservation_id"], res))
    scored.sort(key=lambda t: (-t[0], t[1], t[2]))
    used: set[str] = set()
    assignments = []
    walks = []
    for _score, _rank, _rid, res in scored:
        assigned = False
        for room in rooms:
            if room["room_id"] in used:
                continue
            if room["room_type_id"] != res["room_type_id"]:
                continue
            if room["status"] != "available":
                continue
            if room_blocked(room["room_id"], on_date, maint):
                continue
            used.add(room["room_id"])
            assignments.append(
                {
                    "reservation_id": res["reservation_id"],
                    "guest_id": res["guest_id"],
                    "room_id": room["room_id"],
                    "room_type_id": room["room_type_id"],
                }
            )
            assigned = True
            break
        if assigned:
            continue
        for room in rooms:
            if room["room_id"] in used:
                continue
            if not allowed_upgrade(res["room_type_id"], room["room_type_id"], ranks, rules):
                continue
            if room["status"] != "available":
                continue
            if room_blocked(room["room_id"], on_date, maint):
                continue
            used.add(room["room_id"])
            assignments.append(
                {
                    "reservation_id": res["reservation_id"],
                    "guest_id": res["guest_id"],
                    "room_id": room["room_id"],
                    "room_type_id": room["room_type_id"],
                }
            )
            assigned = True
            break
        if assigned:
            continue
        picked = pick_walk(res["room_type_id"], ranks, rules, costs)
        if picked is None:
            continue
        to_type, cost = picked
        walks.append(
            {
                "reservation_id": res["reservation_id"],
                "guest_id": res["guest_id"],
                "from_type_id": res["room_type_id"],
                "to_type_id": to_type,
                "walk_cost_cents": cost,
            }
        )
    assignments.sort(key=lambda a: a["reservation_id"])
    walks.sort(key=lambda w: (w["walk_cost_cents"], w["reservation_id"]))
    digest = capacity_fingerprint(db_path, meta)
    return {
        "scenario": scenario,
        "engine": "overbookctl",
        "run_stamp": digest[:16],
        "assignments": assignments,
        "walks": walks,
    }


def atlas_total_walk_cost(atlas: dict) -> int:
    return sum(int(row.get("walk_cost_cents", 0)) for row in atlas.get("walks", []))
