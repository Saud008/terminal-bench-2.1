"""Independent seat hold reconciliation reference simulator."""

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


def event_clock(meta: dict) -> str:
    override = os.environ.get("TB3_EVENT_CLOCK")
    return override or meta["event_clock"]


def is_active(hold: sqlite3.Row, clock: str) -> bool:
    return hold["status"] == "active" and clock <= hold["expires_at"]


def hold_snapshot_digest(db_path: Path, meta: dict) -> str:
    conn = _connect(db_path)
    sections = sorted(r["section_id"] for r in conn.execute("SELECT section_id FROM sections").fetchall())
    holds = conn.execute("SELECT hold_id, seat_id FROM seat_holds ORDER BY hold_id").fetchall()
    parts = list(sections) + [f"{h['hold_id']}:{h['seat_id']}" for h in holds]
    payload = "|".join(parts) + "|" + meta["catalog_seed"]
    return hashlib.sha256(payload.encode()).hexdigest()


def run_stamp(scenario: str, digest: str) -> str:
    return hashlib.sha256(f"{digest}|{scenario}".encode()).hexdigest()[:16]


def seats_in_row(seats: list[sqlite3.Row], section_id: str, row_num: int) -> list[sqlite3.Row]:
    out = [s for s in seats if s["section_id"] == section_id and s["row_num"] == row_num]
    out.sort(key=lambda s: s["seat_num"])
    return out


def creates_orphan(row_seats: list[sqlite3.Row], assigned: set[str]) -> bool:
    for i in range(1, len(row_seats) - 1):
        left = row_seats[i - 1]["seat_id"] in assigned
        mid = row_seats[i]["seat_id"] not in assigned
        right = row_seats[i + 1]["seat_id"] in assigned
        if left and mid and right:
            return True
    return False


def allows_adjacency(seat: sqlite3.Row, assigned: set[str], seats: list[sqlite3.Row]) -> bool:
    row = seats_in_row(seats, seat["section_id"], seat["row_num"])
    trial = set(assigned)
    trial.add(seat["seat_id"])
    return not creates_orphan(row, trial)


def allows_a11y(seat: sqlite3.Row, section: sqlite3.Row, assigned: set[str], seats: list[sqlite3.Row]) -> bool:
    if not seat["accessible"]:
        return True
    remaining = 0
    for s in seats:
        if s["section_id"] != seat["section_id"] or not s["accessible"]:
            continue
        if s["seat_id"] not in assigned and s["seat_id"] != seat["seat_id"]:
            remaining += 1
    return remaining >= int(section["accessibility_min"])


def simulate_hold_ledger(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "venue.db"
    meta_path = fixture_root / "scenarios" / scenario / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    clock = event_clock(meta)
    conn = _connect(db_path)
    sections = {r["section_id"]: r for r in conn.execute("SELECT * FROM sections")}
    seats = conn.execute("SELECT * FROM seats ORDER BY seat_id").fetchall()
    seat_map = {r["seat_id"]: r for r in seats}
    orders = {r["order_id"]: r for r in conn.execute("SELECT * FROM orders")}
    holds = conn.execute("SELECT * FROM seat_holds ORDER BY hold_id").fetchall()
    ranked = []
    for h in holds:
        if not is_active(h, clock):
            continue
        o = orders[h["order_id"]]
        ranked.append((int(o["payment_rank"]), o["captured_at"], o["order_id"], h, o))
    ranked.sort(key=lambda t: (t[0], t[1], t[2]))
    assigned: set[str] = set()
    seat_taken: dict[str, str] = {}
    assignments = []
    conflicts = []
    for _rank, _cap, _oid, hold, _order in ranked:
        seat = seat_map.get(hold["seat_id"])
        if seat is None:
            conflicts.append({"hold_id": hold["hold_id"], "seat_id": hold["seat_id"], "reason": "unknown_seat", "severity": 3})
            continue
        if hold["seat_id"] in seat_taken:
            conflicts.append(
                {
                    "hold_id": hold["hold_id"],
                    "seat_id": hold["seat_id"],
                    "reason": "seat_taken:" + seat_taken[hold["seat_id"]],
                    "severity": 2,
                }
            )
            continue
        sec = sections[seat["section_id"]]
        if not allows_adjacency(seat, assigned, seats):
            conflicts.append({"hold_id": hold["hold_id"], "seat_id": hold["seat_id"], "reason": "adjacency_block", "severity": 4})
            continue
        if not allows_a11y(seat, sec, assigned, seats):
            conflicts.append({"hold_id": hold["hold_id"], "seat_id": hold["seat_id"], "reason": "a11y_reserve", "severity": 5})
            continue
        assigned.add(hold["seat_id"])
        seat_taken[hold["seat_id"]] = hold["hold_id"]
        assignments.append(
            {"hold_id": hold["hold_id"], "seat_id": hold["seat_id"], "order_id": hold["order_id"], "status": "held"}
        )
    digest = hold_snapshot_digest(db_path, meta)
    conflicts.sort(key=lambda c: (-c["severity"], c["hold_id"]))
    assignments.sort(key=lambda a: a["seat_id"])
    return {
        "scenario": scenario,
        "engine": "venuetixctl",
        "run_stamp": run_stamp(scenario, digest),
        "assignments": assignments,
        "conflicts": conflicts,
    }


def simulate_snapshot_fingerprint(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "venue.db"
    meta = json.loads((fixture_root / "scenarios" / scenario / "meta.json").read_text(encoding="utf-8"))
    conn = _connect(db_path)
    hold_count = conn.execute("SELECT COUNT(*) AS c FROM seat_holds").fetchone()["c"]
    section_count = conn.execute("SELECT COUNT(*) AS c FROM sections").fetchone()["c"]
    digest = hold_snapshot_digest(db_path, meta)
    return {
        "scenario": scenario,
        "engine": "venuetixctl",
        "hold_snapshot_digest": digest,
        "hold_count": hold_count,
        "section_count": section_count,
    }


# Probe-compatible aliases for independent reference helpers.
reference_reconcile = simulate_hold_ledger
reference_snapshot = simulate_snapshot_fingerprint
