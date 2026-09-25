from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def archive_path(dir_path: str, name: str) -> str:
    return str(Path(dir_path) / f"{name}.json")


def load_archive(path: str, seed: str) -> dict[str, Any]:
    arch = json.loads(Path(path).read_text(encoding="utf-8"))
    if not arch.get("archive_name"):
        raise ValueError("archive_name required")
    _ = seed
    return arch


def scope_accession_id(seed: str, raw: str) -> str:
    x = 2166136261
    for b in (seed + ":" + raw).encode():
        x ^= b
        x = (x * 16777619) & 0xFFFFFFFF
    return f"{raw}-{x:08x}"


def materialize(arch: dict[str, Any], seed: str) -> dict[str, Any]:
    objects: list[dict[str, str]] = []
    for obj in arch.get("objects", []):
        raw = obj.get("accession_id") or obj["ref"]
        objects.append(
            {
                "accession_id": scope_accession_id(seed, raw),
                "title": obj["title"],
                "accession_date": obj["accession_date"],
            }
        )
    ref_to_id: dict[str, str] = {}
    for obj, scoped in zip(arch.get("objects", []), objects, strict=True):
        raw = obj.get("accession_id") or obj["ref"]
        ref_to_id[obj["ref"]] = scope_accession_id(seed, raw)
    focus = ref_to_id[arch["focus_accession_ref"]]
    transfers = [
        {
            "accession_id": ref_to_id[t["accession_ref"]],
            "from_party": t["from_party"],
            "to_party": t["to_party"],
            "transfer_date": t["transfer_date"],
        }
        for t in arch.get("custody_transfers", [])
    ]
    loans = [
        {
            "accession_id": ref_to_id[loan["accession_ref"]],
            "borrower": loan["borrower"],
            "loan_start": loan["loan_start"],
            "loan_end": loan["loan_end"],
            "return_by": loan["return_by"],
        }
        for loan in arch.get("exhibition_loans", [])
    ]
    restorations = [
        {
            "accession_id": ref_to_id[event["accession_ref"]],
            "event_date": event["event_date"],
            "technician": event["technician"],
            "notes": event["notes"],
        }
        for event in arch.get("restoration_events", [])
    ]
    rights = [
        {
            "accession_id": ref_to_id[restriction["accession_ref"]],
            "level": restriction["level"],
            "precedence": restriction["precedence"],
            "expires": restriction["expires"],
        }
        for restriction in arch.get("rights_restrictions", [])
    ]
    return {
        "seed": seed,
        "archive": arch["archive_name"],
        "focus_accession_id": focus,
        "museum_id": arch["museum_id"],
        "as_of_date": arch["as_of_date"],
        "objects": objects,
        "transfers": transfers,
        "loans": loans,
        "restorations": restorations,
        "rights": rights,
    }
