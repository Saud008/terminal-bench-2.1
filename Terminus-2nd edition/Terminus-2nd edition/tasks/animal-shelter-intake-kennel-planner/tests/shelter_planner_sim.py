"""Independent shelter intake reference math for bind/weave/seal contracts."""

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


def intake_date(meta: dict) -> str:
    override = os.environ.get("TB3_INTAKE_DATE")
    return override or meta["intake_date"]


def load_arrivals(path: Path) -> list[sqlite3.Row]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def kennel_quarantined(kennel_id: str, on_date: str, rows: list[sqlite3.Row]) -> bool:
    for row in rows:
        if row["kennel_id"] != kennel_id:
            continue
        if on_date >= row["start_date"] and on_date <= row["end_date"]:
            return True
    return False


def registry_digest(db_path: Path, meta: dict) -> str:
    conn = _connect(db_path)
    kennels = conn.execute("SELECT kennel_id, species_code FROM kennels ORDER BY kennel_id").fetchall()
    quar = conn.execute(
        "SELECT kennel_id, start_date, end_date FROM quarantine_windows ORDER BY kennel_id, start_date"
    ).fetchall()
    kennel_parts = [f"{k['kennel_id']}:{k['species_code']}" for k in kennels]
    quar_parts = [f"{q['kennel_id']}:{q['start_date']}:{q['end_date']}" for q in quar]
    payload = "|".join(kennel_parts) + "|" + meta["catalog_seed"] + "|" + "|".join(quar_parts)
    return hashlib.sha256(payload.encode()).hexdigest()


def hold_precedence(hold_type: str, holds: dict[str, int]) -> int:
    return holds.get(hold_type, 50)


def priority_score(rec: dict, holds: dict[str, int]) -> float:
    base = float(1000 - int(rec["intake_rank"])) * (1.0 - float(rec["surrender_prob"]))
    shield = float(hold_precedence(rec["hold_type"], holds))
    return base + shield * 0.01

def days_remaining(valid_until: str, on_date: str) -> int:
    from datetime import date

    end = date.fromisoformat(valid_until)
    start = date.fromisoformat(on_date)
    return (end - start).days

def vaccine_eligible(rec: dict, on_date: str, policies: dict[str, int]) -> bool:
    min_days = policies.get(rec["species_code"], 0)
    return days_remaining(rec["vacc_valid_until"], on_date) >= min_days


def allowed_upgrade(from_species: str, to_species: str, ranks: dict[str, int], rules: set[tuple[str, str]]) -> bool:
    if (from_species, to_species) not in rules:
        return False
    return ranks[to_species] > ranks[from_species]


def pick_transfer(from_species: str, ranks: dict[str, int], rules: set[tuple[str, str]], penalties: list[sqlite3.Row]):
    choices = []
    for tp in penalties:
        if tp["from_species"] != from_species:
            continue
        if not allowed_upgrade(from_species, tp["to_species"], ranks, rules):
            continue
        choices.append((int(tp["transfer_penalty"]), tp["to_species"]))
    if not choices:
        return None
    choices.sort(key=lambda t: (t[0], t[1]))
    return choices[0][1], choices[0][0]


def reference_bind(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "registry.sqlite"
    meta = json.loads((fixture_root / "scenarios" / scenario / "meta.json").read_text(encoding="utf-8"))
    conn = _connect(db_path)
    kennel_count = conn.execute("SELECT COUNT(*) AS c FROM kennels").fetchone()["c"]
    quar_count = conn.execute("SELECT COUNT(*) AS c FROM quarantine_windows").fetchone()["c"]
    digest = registry_digest(db_path, meta)
    return {
        "scenario": scenario,
        "registry_digest": digest,
        "kennel_count": kennel_count,
        "quarantine_count": quar_count,
    }


def reference_atlas(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "registry.sqlite"
    arrivals_path = fixture_root / "scenarios" / scenario / "arrivals.jsonl"
    meta = json.loads((fixture_root / "scenarios" / scenario / "meta.json").read_text(encoding="utf-8"))
    on_date = intake_date(meta)
    conn = _connect(db_path)
    ranks = {r["species_code"]: int(r["isolation_rank"]) for r in conn.execute("SELECT * FROM species_profiles")}
    holds = {r["hold_type"]: int(r["precedence_rank"]) for r in conn.execute("SELECT * FROM adoption_holds")}
    rules = {(r["from_species"], r["to_species"]) for r in conn.execute("SELECT * FROM kennel_compat_rules")}
    penalties = conn.execute("SELECT * FROM transfer_penalties").fetchall()
    vacc_policies = {
        r["species_code"]: int(r["min_valid_days"])
        for r in conn.execute("SELECT * FROM vaccination_policies")
    }
    quar = conn.execute("SELECT * FROM quarantine_windows").fetchall()
    kennels = [dict(r) for r in conn.execute("SELECT * FROM kennels ORDER BY kennel_id")]
    intakes = load_arrivals(arrivals_path)
    scored = []
    for rec in intakes:
        scored.append((priority_score(rec, holds), int(rec["intake_rank"]), rec["intake_id"], rec))
    scored.sort(key=lambda t: (-t[0], t[1], t[2]))
    used: set[str] = set()
    placements = []
    transfers = []
    for _score, _rank, _iid, rec in scored:
        if not vaccine_eligible(rec, on_date, vacc_policies):
            picked = pick_transfer(rec["species_code"], ranks, rules, penalties)
            if picked is not None:
                to_species, penalty = picked
                transfers.append(
                    {
                        "intake_id": rec["intake_id"],
                        "animal_id": rec["animal_id"],
                        "from_species": rec["species_code"],
                        "to_species": to_species,
                        "transfer_penalty": penalty,
                    }
                )
            continue
        placed = False
        for kennel in kennels:
            if kennel["kennel_id"] in used:
                continue
            if kennel["species_code"] != rec["species_code"]:
                continue
            if int(kennel["capacity"]) <= 0:
                continue
            if kennel_quarantined(kennel["kennel_id"], on_date, quar):
                continue
            used.add(kennel["kennel_id"])
            placements.append(
                {
                    "intake_id": rec["intake_id"],
                    "animal_id": rec["animal_id"],
                    "kennel_id": kennel["kennel_id"],
                    "species_code": kennel["species_code"],
                }
            )
            placed = True
            break
        if placed:
            continue
        for kennel in kennels:
            if kennel["kennel_id"] in used:
                continue
            if not allowed_upgrade(rec["species_code"], kennel["species_code"], ranks, rules):
                continue
            if int(kennel["capacity"]) <= 0:
                continue
            if kennel_quarantined(kennel["kennel_id"], on_date, quar):
                continue
            used.add(kennel["kennel_id"])
            placements.append(
                {
                    "intake_id": rec["intake_id"],
                    "animal_id": rec["animal_id"],
                    "kennel_id": kennel["kennel_id"],
                    "species_code": kennel["species_code"],
                }
            )
            placed = True
            break
        if placed:
            continue
        picked = pick_transfer(rec["species_code"], ranks, rules, penalties)
        if picked is None:
            continue
        to_species, penalty = picked
        transfers.append(
            {
                "intake_id": rec["intake_id"],
                "animal_id": rec["animal_id"],
                "from_species": rec["species_code"],
                "to_species": to_species,
                "transfer_penalty": penalty,
            }
        )
    placements.sort(key=lambda a: a["intake_id"])
    transfers.sort(key=lambda t: (t["transfer_penalty"], t["intake_id"]))
    digest = registry_digest(db_path, meta)
    return {
        "scenario": scenario,
        "engine": "intakectl",
        "run_stamp": digest[:16],
        "placements": placements,
        "transfers": transfers,
    }
