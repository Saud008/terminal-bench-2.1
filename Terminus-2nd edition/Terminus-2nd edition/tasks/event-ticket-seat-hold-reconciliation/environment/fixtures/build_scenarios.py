#!/usr/bin/env python3
"""Build SQLite venue scenarios with seeded randomized ids."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT
HIDDEN_ROOT = Path(os.environ.get("VENUETIX_HIDDEN_ROOT", "")) if os.environ.get("VENUETIX_HIDDEN_ROOT") else None


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
        CREATE TABLE scenario_meta (scenario TEXT, event_clock TEXT, catalog_seed TEXT);
        CREATE TABLE sections (section_id TEXT, name TEXT, row_count INTEGER, accessibility_min INTEGER);
        CREATE TABLE seats (seat_id TEXT, section_id TEXT, row_num INTEGER, seat_num INTEGER, accessible INTEGER);
        CREATE TABLE orders (order_id TEXT, patron_id TEXT, payment_rank INTEGER, captured_at TEXT);
        CREATE TABLE seat_holds (hold_id TEXT, order_id TEXT, seat_id TEXT, expires_at TEXT, status TEXT);
        """
    )
    cur.execute(
        "INSERT INTO scenario_meta VALUES (?,?,?)",
        (meta["scenario"], meta["event_clock"], meta["catalog_seed"]),
    )
    for s in rows["sections"]:
        cur.execute(
            "INSERT INTO sections VALUES (?,?,?,?)",
            (s["section_id"], s["name"], s["row_count"], s["accessibility_min"]),
        )
    for seat in rows["seats"]:
        cur.execute(
            "INSERT INTO seats VALUES (?,?,?,?,?)",
            (seat["seat_id"], seat["section_id"], seat["row_num"], seat["seat_num"], 1 if seat["accessible"] else 0),
        )
    for o in rows["orders"]:
        cur.execute(
            "INSERT INTO orders VALUES (?,?,?,?)",
            (o["order_id"], o["patron_id"], o["payment_rank"], o["captured_at"]),
        )
    for h in rows["holds"]:
        cur.execute(
            "INSERT INTO seat_holds VALUES (?,?,?,?,?)",
            (h["hold_id"], h["order_id"], h["seat_id"], h["expires_at"], h["status"]),
        )
    conn.commit()
    conn.close()


def base_venue(seed: str) -> dict:
    ids = seed_ids(seed, ["sec-a", "ord-1", "ord-2", "pat-1", "pat-2", "h-1", "h-2"])
    seats = []
    for row in (1, 2):
        for num in (1, 2, 3):
            sid = seed_ids(seed, [f"s-{row}-{num}"])[f"s-{row}-{num}"]
            seats.append(
                {
                    "seat_id": sid,
                    "section_id": ids["sec-a"],
                    "row_num": row,
                    "seat_num": num,
                    "accessible": num == 1,
                }
            )
    return {
        "sections": [{"section_id": ids["sec-a"], "name": "Orchestra", "row_count": 2, "accessibility_min": 1}],
        "seats": seats,
        "orders": [
            {"order_id": ids["ord-1"], "patron_id": ids["pat-1"], "payment_rank": 10, "captured_at": "2026-04-01T10:00:00Z"},
            {"order_id": ids["ord-2"], "patron_id": ids["pat-2"], "payment_rank": 20, "captured_at": "2026-04-01T11:00:00Z"},
        ],
        "holds": [
            {
                "hold_id": ids["h-1"],
                "order_id": ids["ord-1"],
                "seat_id": seats[0]["seat_id"],
                "expires_at": "2026-04-05T23:59:59Z",
                "status": "active",
            },
            {
                "hold_id": ids["h-2"],
                "order_id": ids["ord-2"],
                "seat_id": seats[3]["seat_id"],
                "expires_at": "2026-04-05T23:59:59Z",
                "status": "active",
            },
        ],
    }


def scenario_clean(seed: str) -> dict:
    return base_venue(seed)


def scenario_expiry_block(seed: str) -> dict:
    base = base_venue(seed)
    base["holds"][0]["expires_at"] = "2026-04-01T08:00:00Z"
    return base


def scenario_payment_precedence(seed: str) -> dict:
    base = base_venue(seed)
    seat = base["seats"][1]["seat_id"]
    ids = seed_ids(seed, ["ord-lo", "ord-hi", "h-lo", "h-hi"])
    base["orders"].extend(
        [
            {"order_id": ids["ord-lo"], "patron_id": base["orders"][0]["patron_id"], "payment_rank": 5, "captured_at": "2026-04-02T09:00:00Z"},
            {"order_id": ids["ord-hi"], "patron_id": base["orders"][1]["patron_id"], "payment_rank": 15, "captured_at": "2026-04-02T08:00:00Z"},
        ]
    )
    base["holds"].extend(
        [
            {"hold_id": ids["h-lo"], "order_id": ids["ord-lo"], "seat_id": seat, "expires_at": "2026-04-06T00:00:00Z", "status": "active"},
            {"hold_id": ids["h-hi"], "order_id": ids["ord-hi"], "seat_id": seat, "expires_at": "2026-04-06T00:00:00Z", "status": "active"},
        ]
    )
    return base


def scenario_adjacency_gap(seed: str) -> dict:
    base = base_venue(seed)
    row1 = [s for s in base["seats"] if s["row_num"] == 1]
    row1.sort(key=lambda s: s["seat_num"])
    ids = seed_ids(seed, ["ord-a", "ord-c", "h-a", "h-c"])
    base["orders"].extend(
        [
            {"order_id": ids["ord-a"], "patron_id": "pat-a", "payment_rank": 1, "captured_at": "2026-04-01T12:00:00Z"},
            {"order_id": ids["ord-c"], "patron_id": "pat-c", "payment_rank": 2, "captured_at": "2026-04-01T13:00:00Z"},
        ]
    )
    base["holds"] = [
        {"hold_id": ids["h-a"], "order_id": ids["ord-a"], "seat_id": row1[0]["seat_id"], "expires_at": "2026-04-07T00:00:00Z", "status": "active"},
        {"hold_id": ids["h-c"], "order_id": ids["ord-c"], "seat_id": row1[2]["seat_id"], "expires_at": "2026-04-07T00:00:00Z", "status": "active"},
    ]
    return base


def scenario_a11y_reserve(seed: str) -> dict:
    base = base_venue(seed)
    acc = [s for s in base["seats"] if s["accessible"]]
    ids = seed_ids(seed, ["ord-x", "h-x"])
    base["sections"][0]["accessibility_min"] = 2
    base["holds"] = [
        {"hold_id": ids["h-x"], "order_id": ids["ord-x"], "seat_id": acc[0]["seat_id"], "expires_at": "2026-04-08T00:00:00Z", "status": "active"},
    ]
    base["orders"].append({"order_id": ids["ord-x"], "patron_id": "pat-x", "payment_rank": 1, "captured_at": "2026-04-03T09:00:00Z"})
    return base


def scenario_multi_section(seed: str) -> dict:
    base = base_venue(seed)
    ids = seed_ids(seed, ["sec-b", "ord-b", "h-b"])
    extra_seats = []
    for num in (1, 2):
        sid = seed_ids(seed, [f"sb-{num}"])[f"sb-{num}"]
        extra_seats.append({"seat_id": sid, "section_id": ids["sec-b"], "row_num": 1, "seat_num": num, "accessible": False})
    base["sections"].append({"section_id": ids["sec-b"], "name": "Balcony", "row_count": 1, "accessibility_min": 0})
    base["seats"].extend(extra_seats)
    base["orders"].append({"order_id": ids["ord-b"], "patron_id": "pat-b", "payment_rank": 3, "captured_at": "2026-04-04T10:00:00Z"})
    base["holds"].append(
        {"hold_id": ids["h-b"], "order_id": ids["ord-b"], "seat_id": extra_seats[0]["seat_id"], "expires_at": "2026-04-09T00:00:00Z", "status": "active"}
    )
    return base


def scenario_stable_ledger(seed: str) -> dict:
    return base_venue(seed)


def scenario_expiry_boundary(seed: str) -> dict:
    base = base_venue(seed)
    base["holds"][0]["expires_at"] = "2026-04-05T12:00:00Z"
    base["meta_clock"] = "2026-04-05T12:00:00Z"
    return base


def scenario_a11y_hidden(seed: str) -> dict:
    base = base_venue(seed)
    acc = [s for s in base["seats"] if s["accessible"]]
    base["sections"][0]["accessibility_min"] = len(acc)
    ids = seed_ids(seed, ["ord-z", "h-z"])
    base["orders"] = [{"order_id": ids["ord-z"], "patron_id": "pat-z", "payment_rank": 1, "captured_at": "2026-04-05T10:00:00Z"}]
    base["holds"] = [
        {"hold_id": ids["h-z"], "order_id": ids["ord-z"], "seat_id": acc[0]["seat_id"], "expires_at": "2026-04-10T00:00:00Z", "status": "active"},
    ]
    return base


BUILDERS = {
    "clean-venue": scenario_clean,
    "expiry-block": scenario_expiry_block,
    "payment-precedence": scenario_payment_precedence,
    "adjacency-gap": scenario_adjacency_gap,
    "a11y-reserve": scenario_a11y_reserve,
    "stable-rerun": scenario_stable_ledger,
    "multi-section": scenario_multi_section,
    "stable-ledger": scenario_stable_ledger,
    "expiry-boundary-trap": scenario_expiry_boundary,
    "a11y-hidden-trap": scenario_a11y_hidden,
}


def emit(name: str, out_root: Path) -> None:
    seed = hashlib.sha256(name.encode()).hexdigest()[:16]
    builder = BUILDERS[name]
    rows = builder(seed)
    event_clock = rows.pop("meta_clock", "2026-04-05T12:00:00Z")
    meta = {"scenario": name, "event_clock": event_clock, "catalog_seed": seed}
    dest = out_root / "scenarios" / name
    write_db(dest / "venue.db", meta, rows)
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


BUNDLED = (
    "clean-venue",
    "expiry-block",
    "payment-precedence",
    "adjacency-gap",
    "a11y-reserve",
    "stable-rerun",
    "multi-section",
    "stable-ledger",
)
HIDDEN = (
    "expiry-boundary-trap",
    "a11y-hidden-trap",
)


def main() -> None:
    targets = [DEFAULT_OUT]
    if HIDDEN_ROOT is not None and str(HIDDEN_ROOT):
        targets.append(HIDDEN_ROOT)
    for out_root in targets:
        names = list(BUNDLED) if out_root == DEFAULT_OUT else list(HIDDEN)
        for name in names:
            emit(name, out_root)


if __name__ == "__main__":
    main()
