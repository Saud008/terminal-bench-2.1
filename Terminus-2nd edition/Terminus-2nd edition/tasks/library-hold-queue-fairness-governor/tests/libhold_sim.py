"""Independent hold queue fairness reference simulator."""

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


def reconcile_date(meta: dict) -> str:
    override = os.environ.get("TB3_RECONCILE_DATE")
    return override or meta["reconcile_date"]


def is_suspended(patron_id: str, on_date: str, rows: list[sqlite3.Row]) -> bool:
    for row in rows:
        if row["patron_id"] != patron_id:
            continue
        if on_date >= row["start_date"] and on_date <= row["end_date"]:
            return True
    return False


def rollup_fingerprint(db_path: Path, meta: dict) -> str:
    conn = _connect(db_path)
    patrons = [r["patron_id"] for r in conn.execute("SELECT DISTINCT patron_id FROM patrons").fetchall()]
    patrons.sort()
    holds = conn.execute(
        "SELECT request_id, item_id FROM hold_requests ORDER BY request_id"
    ).fetchall()
    parts = list(patrons) + [f"{h['request_id']}:{h['item_id']}" for h in holds]
    payload = "|".join(parts) + "|" + meta["catalog_seed"]
    return hashlib.sha256(payload.encode()).hexdigest()


def run_stamp(scenario: str, digest: str) -> str:
    return hashlib.sha256(f"{digest}|{scenario}".encode()).hexdigest()[:16]


def simulate_hold_assignments(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "library.db"
    meta_path = fixture_root / "scenarios" / scenario / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    on_date = reconcile_date(meta)
    conn = _connect(db_path)
    branches = {r["branch_id"]: r for r in conn.execute("SELECT * FROM branches")}
    policies = {r["class_name"]: int(r["rank"]) for r in conn.execute("SELECT * FROM priority_policies")}
    patrons = {r["patron_id"]: r for r in conn.execute("SELECT * FROM patrons")}
    suspensions = conn.execute("SELECT * FROM suspension_windows").fetchall()
    holds = conn.execute("SELECT * FROM hold_requests").fetchall()
    copies = [dict(r) for r in conn.execute("SELECT * FROM item_copies")]
    ranked = []
    for h in holds:
        if is_suspended(h["patron_id"], on_date, suspensions):
            continue
        patron = patrons[h["patron_id"]]
        ranked.append(
            (
                policies[patron["priority_class"]],
                h["hold_date"],
                h["patron_id"],
                h,
            )
        )
    ranked.sort(key=lambda t: (t[0], t[1], t[2]))
    used: set[str] = set()
    assignments = []
    queue_pos = 1
    for _rank, _date, _patron, hold in ranked:
        pick = _select_copy(copies, hold["item_id"], hold["pickup_branch_id"], branches, used)
        if pick is None:
            continue
        used.add(pick["copy_id"])
        assignments.append(
            {
                "queue_pos": queue_pos,
                "patron_id": hold["patron_id"],
                "request_id": hold["request_id"],
                "copy_id": pick["copy_id"],
                "branch_id": pick["branch_id"],
            }
        )
        queue_pos += 1
    digest = rollup_fingerprint(db_path, meta)
    assignments.sort(key=lambda a: (a["queue_pos"], a["patron_id"]))
    return {
        "scenario": scenario,
        "engine": "holdfairctl",
        "run_stamp": run_stamp(scenario, digest),
        "assignments": assignments,
    }


def _select_copy(copies, item_id, pickup_branch, branches, used):
    candidates = []
    for c in copies:
        if c["copy_id"] in used:
            continue
        if c["item_id"] != item_id or c["status"] != "available":
            continue
        candidates.append(c)
    candidates.sort(key=lambda c: c["copy_id"])
    for c in candidates:
        if c["branch_id"] == pickup_branch:
            return c
    for c in candidates:
        br = branches[c["branch_id"]]
        if br["allows_interbranch_transfer"]:
            return c
    return None


def build_rollup_snapshot(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "library.db"
    meta = json.loads((fixture_root / "scenarios" / scenario / "meta.json").read_text(encoding="utf-8"))
    conn = _connect(db_path)
    hold_count = conn.execute("SELECT COUNT(*) AS c FROM hold_requests").fetchone()["c"]
    patron_count = conn.execute("SELECT COUNT(*) AS c FROM patrons").fetchone()["c"]
    digest = rollup_fingerprint(db_path, meta)
    return {
        "scenario": scenario,
        "engine": "holdfairctl",
        "rollup_fingerprint": digest,
        "hold_request_count": hold_count,
        "patron_count": patron_count,
    }
