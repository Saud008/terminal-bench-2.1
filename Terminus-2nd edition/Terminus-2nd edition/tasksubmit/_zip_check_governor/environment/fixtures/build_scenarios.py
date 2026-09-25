#!/usr/bin/env python3
"""Build SQLite library scenarios with seeded randomized ids."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT

BUNDLED = (
    "clean-queue",
    "branch-routing",
    "suspension-block",
    "priority-tiers",
    "stamp-rerun",
    "multi-hold",
    "interbranch-transfer",
    "stable-atlas",
)


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
        CREATE TABLE scenario_meta (scenario TEXT, reconcile_date TEXT, catalog_seed TEXT);
        CREATE TABLE branches (branch_id TEXT, name TEXT, allows_interbranch_transfer INTEGER);
        CREATE TABLE patrons (patron_id TEXT, home_branch_id TEXT, priority_class TEXT);
        CREATE TABLE hold_requests (request_id TEXT, patron_id TEXT, item_id TEXT, pickup_branch_id TEXT, hold_date TEXT);
        CREATE TABLE item_copies (copy_id TEXT, item_id TEXT, branch_id TEXT, status TEXT);
        CREATE TABLE suspension_windows (patron_id TEXT, start_date TEXT, end_date TEXT);
        CREATE TABLE priority_policies (class_name TEXT, rank INTEGER);
        """
    )
    cur.execute(
        "INSERT INTO scenario_meta VALUES (?,?,?)",
        (meta["scenario"], meta["reconcile_date"], meta["catalog_seed"]),
    )
    for b in rows["branches"]:
        cur.execute(
            "INSERT INTO branches VALUES (?,?,?)",
            (b["branch_id"], b["name"], 1 if b["allows_interbranch_transfer"] else 0),
        )
    for p in rows["patrons"]:
        cur.execute(
            "INSERT INTO patrons VALUES (?,?,?)",
            (p["patron_id"], p["home_branch_id"], p["priority_class"]),
        )
    for h in rows["holds"]:
        cur.execute(
            "INSERT INTO hold_requests VALUES (?,?,?,?,?)",
            (h["request_id"], h["patron_id"], h["item_id"], h["pickup_branch_id"], h["hold_date"]),
        )
    for c in rows["copies"]:
        cur.execute(
            "INSERT INTO item_copies VALUES (?,?,?,?)",
            (c["copy_id"], c["item_id"], c["branch_id"], c["status"]),
        )
    for s in rows.get("suspensions", []):
        cur.execute(
            "INSERT INTO suspension_windows VALUES (?,?,?)",
            (s["patron_id"], s["start_date"], s["end_date"]),
        )
    for pol in rows["policies"]:
        cur.execute(
            "INSERT INTO priority_policies VALUES (?,?)",
            (pol["class_name"], pol["rank"]),
        )
    conn.commit()
    conn.close()


def scenario_clean(seed: str) -> dict:
    ids = seed_ids(seed, ["br-a", "br-b", "pat-1", "pat-2", "item-x", "cp-1", "cp-2", "req-1", "req-2"])
    return {
        "branches": [
            {"branch_id": ids["br-a"], "name": "North", "allows_interbranch_transfer": True},
            {"branch_id": ids["br-b"], "name": "South", "allows_interbranch_transfer": False},
        ],
        "patrons": [
            {"patron_id": ids["pat-1"], "home_branch_id": ids["br-a"], "priority_class": "standard"},
            {"patron_id": ids["pat-2"], "home_branch_id": ids["br-b"], "priority_class": "standard"},
        ],
        "policies": [
            {"class_name": "standard", "rank": 10},
            {"class_name": "teacher", "rank": 5},
        ],
        "holds": [
            {
                "request_id": ids["req-1"],
                "patron_id": ids["pat-1"],
                "item_id": ids["item-x"],
                "pickup_branch_id": ids["br-a"],
                "hold_date": "2026-03-01",
            },
            {
                "request_id": ids["req-2"],
                "patron_id": ids["pat-2"],
                "item_id": ids["item-x"],
                "pickup_branch_id": ids["br-b"],
                "hold_date": "2026-03-02",
            },
        ],
        "copies": [
            {"copy_id": ids["cp-1"], "item_id": ids["item-x"], "branch_id": ids["br-a"], "status": "available"},
            {"copy_id": ids["cp-2"], "item_id": ids["item-x"], "branch_id": ids["br-b"], "status": "available"},
        ],
        "suspensions": [],
    }


def scenario_branch_routing(seed: str) -> dict:
    base = scenario_clean(seed)
    ids = seed_ids(seed, ["pat-3", "req-3", "cp-3"])
    base["patrons"].append({"patron_id": ids["pat-3"], "home_branch_id": base["branches"][0]["branch_id"], "priority_class": "standard"})
    base["holds"].append(
        {
            "request_id": ids["req-3"],
            "patron_id": ids["pat-3"],
            "item_id": base["copies"][0]["item_id"],
            "pickup_branch_id": base["branches"][1]["branch_id"],
            "hold_date": "2026-03-03",
        }
    )
    base["copies"].append(
        {"copy_id": ids["cp-3"], "item_id": base["copies"][0]["item_id"], "branch_id": base["branches"][0]["branch_id"], "status": "available"}
    )
    return base


def scenario_suspension_block(seed: str) -> dict:
    base = scenario_clean(seed)
    patron = base["patrons"][0]["patron_id"]
    base["suspensions"] = [{"patron_id": patron, "start_date": "2026-03-01", "end_date": "2026-03-05"}]
    return base


def scenario_priority_tiers(seed: str) -> dict:
    base = scenario_clean(seed)
    ids = seed_ids(seed, ["pat-t", "pat-s", "req-t", "req-s"])
    item = base["copies"][0]["item_id"]
    br = base["branches"][0]["branch_id"]
    base["patrons"].extend(
        [
            {"patron_id": ids["pat-t"], "home_branch_id": br, "priority_class": "teacher"},
            {"patron_id": ids["pat-s"], "home_branch_id": br, "priority_class": "standard"},
        ]
    )
    base["holds"].extend(
        [
            {
                "request_id": ids["req-s"],
                "patron_id": ids["pat-s"],
                "item_id": item,
                "pickup_branch_id": br,
                "hold_date": "2026-03-01",
            },
            {
                "request_id": ids["req-t"],
                "patron_id": ids["pat-t"],
                "item_id": item,
                "pickup_branch_id": br,
                "hold_date": "2026-03-04",
            },
        ]
    )
    base["copies"] = [base["copies"][0]]
    return base


def scenario_multi_hold(seed: str) -> dict:
    base = scenario_clean(seed)
    ids = seed_ids(seed, ["item-y", "cp-y", "req-y"])
    base["holds"].append(
        {
            "request_id": ids["req-y"],
            "patron_id": base["patrons"][0]["patron_id"],
            "item_id": ids["item-y"],
            "pickup_branch_id": base["branches"][0]["branch_id"],
            "hold_date": "2026-03-01",
        }
    )
    base["copies"].append(
        {"copy_id": ids["cp-y"], "item_id": ids["item-y"], "branch_id": base["branches"][0]["branch_id"], "status": "available"}
    )
    return base


def scenario_interbranch(seed: str) -> dict:
    base = scenario_branch_routing(seed)
    for c in base["copies"]:
        if c["branch_id"] == base["branches"][1]["branch_id"]:
            c["status"] = "assigned"
    return base


def scenario_stable_atlas(seed: str) -> dict:
    return scenario_clean(seed)


BUILDERS = {
    "clean-queue": scenario_clean,
    "branch-routing": scenario_branch_routing,
    "suspension-block": scenario_suspension_block,
    "priority-tiers": scenario_priority_tiers,
    "stamp-rerun": scenario_stable_atlas,
    "multi-hold": scenario_multi_hold,
    "interbranch-transfer": scenario_interbranch,
    "stable-atlas": scenario_stable_atlas,
}


def emit(name: str, out_root: Path) -> None:
    seed = hashlib.sha256(name.encode()).hexdigest()[:16]
    builder = BUILDERS[name]
    rows = builder(seed)
    reconcile_date = rows.pop("meta_date", "2026-03-05")
    meta = {"scenario": name, "reconcile_date": reconcile_date, "catalog_seed": seed}
    dest = out_root / "scenarios" / name
    write_db(dest / "library.db", meta, rows)
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for name in BUNDLED:
        emit(name, DEFAULT_OUT)


if __name__ == "__main__":
    main()
