#!/usr/bin/env python3
"""Build registry.sqlite + arrivals.jsonl scenarios with seeded randomized ids."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT
HIDDEN_ROOT = Path(os.environ.get("ASIQ_HIDDEN_ROOT", "")) if os.environ.get("ASIQ_HIDDEN_ROOT") else None

BUNDLED = (
    "clean-intake",
    "overflow-single",
    "quarantine-block",
    "hold-precedence",
    "species-upgrade",
    "priority-ranking",
    "transfer-penalty-tie",
    "stable-rerun",
)

HIDDEN = (
    "quarantine-boundary-trap",
    "transfer-penalty-hidden-trap",
)


def seed_ids(seed: str, labels: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for label in labels:
        digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()
        out[label] = f"{label[:3]}-{digest[:8]}"
    return out


def write_registry_db(path: Path, meta: dict, rows: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE scenario_meta (scenario TEXT, intake_date TEXT, catalog_seed TEXT);
        CREATE TABLE species_profiles (species_code TEXT, name TEXT, isolation_rank INTEGER);
        CREATE TABLE kennels (kennel_id TEXT, species_code TEXT, capacity INTEGER, zone TEXT);
        CREATE TABLE quarantine_windows (kennel_id TEXT, start_date TEXT, end_date TEXT);
        CREATE TABLE vaccination_policies (species_code TEXT, min_valid_days INTEGER);
        CREATE TABLE kennel_compat_rules (from_species TEXT, to_species TEXT);
        CREATE TABLE transfer_penalties (from_species TEXT, to_species TEXT, transfer_penalty INTEGER);
        CREATE TABLE adoption_holds (hold_type TEXT, precedence_rank INTEGER);
        """
    )
    cur.execute(
        "INSERT INTO scenario_meta VALUES (?,?,?)",
        (meta["scenario"], meta["intake_date"], meta["catalog_seed"]),
    )
    for sp in rows["species"]:
        cur.execute("INSERT INTO species_profiles VALUES (?,?,?)", (sp["species_code"], sp["name"], sp["isolation_rank"]))
    for k in rows["kennels"]:
        cur.execute("INSERT INTO kennels VALUES (?,?,?,?)", (k["kennel_id"], k["species_code"], k["capacity"], k["zone"]))
    for q in rows.get("quarantine", []):
        cur.execute("INSERT INTO quarantine_windows VALUES (?,?,?)", (q["kennel_id"], q["start_date"], q["end_date"]))
    for pol in rows["vaccination"]:
        cur.execute("INSERT INTO vaccination_policies VALUES (?,?)", (pol["species_code"], pol["min_valid_days"]))
    for rule in rows.get("compat", []):
        cur.execute("INSERT INTO kennel_compat_rules VALUES (?,?)", (rule["from_species"], rule["to_species"]))
    for tp in rows.get("penalties", []):
        cur.execute(
            "INSERT INTO transfer_penalties VALUES (?,?,?)",
            (tp["from_species"], tp["to_species"], tp["transfer_penalty"]),
        )
    for hold in rows["holds"]:
        cur.execute("INSERT INTO adoption_holds VALUES (?,?)", (hold["hold_type"], hold["precedence_rank"]))
    conn.commit()
    conn.close()


def write_arrivals_jsonl(path: Path, intakes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(rec, separators=(",", ":")) for rec in intakes]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def base_species(seed: str) -> dict:
    ids = seed_ids(seed, ["dog", "cat", "rab"])
    return {
        "dog": {"species_code": ids["dog"], "name": "canine", "isolation_rank": 1},
        "cat": {"species_code": ids["cat"], "name": "feline", "isolation_rank": 2},
        "rab": {"species_code": ids["rab"], "name": "rabbit", "isolation_rank": 3},
    }


def default_holds() -> list[dict]:
    return [
        {"hold_type": "legal_hold", "precedence_rank": 1},
        {"hold_type": "adoption_pending", "precedence_rank": 5},
        {"hold_type": "stray", "precedence_rank": 20},
    ]


def default_vaccination(species: dict) -> list[dict]:
    return [
        {"species_code": species["dog"]["species_code"], "min_valid_days": 30},
        {"species_code": species["cat"]["species_code"], "min_valid_days": 21},
        {"species_code": species["rab"]["species_code"], "min_valid_days": 14},
    ]


def default_penalties(species: dict) -> list[dict]:
    dog, cat, rab = species["dog"]["species_code"], species["cat"]["species_code"], species["rab"]["species_code"]
    return [
        {"from_species": dog, "to_species": cat, "transfer_penalty": 4500},
        {"from_species": dog, "to_species": rab, "transfer_penalty": 9000},
        {"from_species": cat, "to_species": rab, "transfer_penalty": 5000},
    ]


def default_compat(species: dict) -> list[dict]:
    dog, cat, rab = species["dog"]["species_code"], species["cat"]["species_code"], species["rab"]["species_code"]
    return [
        {"from_species": dog, "to_species": cat},
        {"from_species": dog, "to_species": rab},
        {"from_species": cat, "to_species": rab},
    ]


def scenario_clean(seed: str) -> dict:
    species = base_species(seed)
    ids = seed_ids(seed, ["kn-1", "kn-2", "an-1", "an-2", "in-1", "in-2"])
    dog = species["dog"]["species_code"]
    return {
        "species": list(species.values()),
        "kennels": [
            {"kennel_id": ids["kn-1"], "species_code": dog, "capacity": 1, "zone": "north"},
            {"kennel_id": ids["kn-2"], "species_code": dog, "capacity": 1, "zone": "south"},
        ],
        "holds": default_holds(),
        "vaccination": default_vaccination(species),
        "compat": default_compat(species),
        "penalties": default_penalties(species),
        "intakes": [
            {
                "intake_id": ids["in-1"], "animal_id": ids["an-1"], "species_code": dog,
                "vacc_valid_until": "2026-12-31", "hold_type": "stray",
                "surrender_prob": 0.05, "intake_rank": 1,
            },
            {
                "intake_id": ids["in-2"], "animal_id": ids["an-2"], "species_code": dog,
                "vacc_valid_until": "2026-12-31", "hold_type": "adoption_pending",
                "surrender_prob": 0.10, "intake_rank": 2,
            },
        ],
        "quarantine": [],
    }


def scenario_overflow(seed: str) -> dict:
    base = scenario_clean(seed)
    ids = seed_ids(seed, ["an-3", "in-3"])
    dog = base["species"][0]["species_code"]
    base["intakes"].append(
        {
            "intake_id": ids["in-3"], "animal_id": ids["an-3"], "species_code": dog,
            "vacc_valid_until": "2026-12-31", "hold_type": "stray",
            "surrender_prob": 0.80, "intake_rank": 3,
        }
    )
    return base


def scenario_quarantine(seed: str) -> dict:
    base = scenario_clean(seed)
    base["kennels"] = base["kennels"][:1]
    base["quarantine"] = [
        {"kennel_id": base["kennels"][0]["kennel_id"], "start_date": "2026-04-01", "end_date": "2026-04-10"},
    ]
    return base


def scenario_hold(seed: str) -> dict:
    base = scenario_overflow(seed)
    base["intakes"][0]["hold_type"] = "legal_hold"
    base["intakes"][0]["surrender_prob"] = 0.02
    base["intakes"][2]["surrender_prob"] = 0.90
    return base


def scenario_species_upgrade(seed: str) -> dict:
    base = scenario_clean(seed)
    species = {s["name"]: s for s in base["species"]}
    ids = seed_ids(seed, ["kn-c", "in-c", "an-c"])
    base["kennels"] = [
        {"kennel_id": ids["kn-c"], "species_code": species["feline"]["species_code"], "capacity": 1, "zone": "east"},
    ]
    base["intakes"] = [
        {
            "intake_id": ids["in-c"], "animal_id": ids["an-c"],
            "species_code": species["canine"]["species_code"],
            "vacc_valid_until": "2026-12-31", "hold_type": "adoption_pending",
            "surrender_prob": 0.05, "intake_rank": 1,
        }
    ]
    return base


def scenario_priority(seed: str) -> dict:
    base = scenario_overflow(seed)
    base["intakes"][1]["surrender_prob"] = 0.05
    base["intakes"][2]["surrender_prob"] = 0.95
    base["intakes"][2]["intake_rank"] = 2
    base["intakes"][1]["intake_rank"] = 3
    return base


def scenario_transfer_tie(seed: str) -> dict:
    base = scenario_overflow(seed)
    species = {s["name"]: s for s in base["species"]}
    dog = species["canine"]["species_code"]
    cat = species["feline"]["species_code"]
    rab = species["rabbit"]["species_code"]
    base["kennels"] = []
    base["penalties"] = [
        {"from_species": dog, "to_species": cat, "transfer_penalty": 3000},
        {"from_species": dog, "to_species": rab, "transfer_penalty": 3000},
    ]
    return base


def scenario_stable_rerun(seed: str) -> dict:
    return scenario_clean(seed)


def scenario_quar_boundary(seed: str) -> dict:
    base = scenario_clean(seed)
    base["quarantine"] = [
        {"kennel_id": base["kennels"][0]["kennel_id"], "start_date": "2026-04-01", "end_date": "2026-04-05"},
    ]
    base["meta_date"] = "2026-04-05"
    return base


def scenario_transfer_hidden(seed: str) -> dict:
    base = scenario_overflow(seed)
    species = {s["name"]: s for s in base["species"]}
    dog = species["canine"]["species_code"]
    cat = species["feline"]["species_code"]
    rab = species["rabbit"]["species_code"]
    base["kennels"] = []
    base["penalties"] = [
        {"from_species": dog, "to_species": rab, "transfer_penalty": 2000},
        {"from_species": dog, "to_species": cat, "transfer_penalty": 2500},
    ]
    base["intakes"][2]["surrender_prob"] = 0.99
    return base


BUILDERS = {
    "clean-intake": scenario_clean,
    "overflow-single": scenario_overflow,
    "quarantine-block": scenario_quarantine,
    "hold-precedence": scenario_hold,
    "species-upgrade": scenario_species_upgrade,
    "priority-ranking": scenario_priority,
    "transfer-penalty-tie": scenario_transfer_tie,
    "stable-rerun": scenario_stable_rerun,
    "quarantine-boundary-trap": scenario_quar_boundary,
    "transfer-penalty-hidden-trap": scenario_transfer_hidden,
}


def emit(name: str, out_root: Path) -> None:
    seed = hashlib.sha256(name.encode()).hexdigest()[:16]
    rows = BUILDERS[name](seed)
    intakes = rows.pop("intakes")
    intake_date = rows.pop("meta_date", "2026-04-05")
    meta = {"scenario": name, "intake_date": intake_date, "catalog_seed": seed}
    dest = out_root / "scenarios" / name
    write_registry_db(dest / "registry.sqlite", meta, rows)
    write_arrivals_jsonl(dest / "arrivals.jsonl", intakes)
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


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
