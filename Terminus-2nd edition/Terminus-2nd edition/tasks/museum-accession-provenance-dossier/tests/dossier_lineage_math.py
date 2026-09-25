"""Independent dossier math for musdoss — not part of the agent contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _scope_accession(seed: str, raw: str) -> str:
    x = 2166136261
    for b in (seed + ":" + raw).encode():
        x ^= b
        x = (x * 16777619) & 0xFFFFFFFF
    return f"{raw}-{x:08x}"


def _materialize(arch: dict[str, Any], seed: str) -> dict[str, Any]:
    objects = []
    ref_to_id: dict[str, str] = {}
    for o in arch["objects"]:
        raw = o.get("accession_id") or o["ref"]
        aid = _scope_accession(seed, raw)
        objects.append(
            {
                "accession_id": aid,
                "title": o["title"],
                "accession_date": o["accession_date"],
            }
        )
        ref_to_id[o["ref"]] = aid
    focus = ref_to_id[arch["focus_accession_ref"]]
    transfers = [
        {
            "accession_id": ref_to_id[t["accession_ref"]],
            "from_party": t["from_party"],
            "to_party": t["to_party"],
            "transfer_date": t["transfer_date"],
        }
        for t in arch.get("custody_transfers") or []
    ]
    loans = [
        {
            "accession_id": ref_to_id[loan["accession_ref"]],
            "borrower": loan["borrower"],
            "loan_start": loan["loan_start"],
            "loan_end": loan["loan_end"],
            "return_by": loan["return_by"],
        }
        for loan in arch.get("exhibition_loans") or []
    ]
    restorations = [
        {
            "accession_id": ref_to_id[r["accession_ref"]],
            "event_date": r["event_date"],
            "technician": r["technician"],
            "notes": r["notes"],
        }
        for r in arch.get("restoration_events") or []
    ]
    rights = [
        {
            "accession_id": ref_to_id[r["accession_ref"]],
            "level": r["level"],
            "precedence": int(r["precedence"]),
            "expires": r["expires"],
        }
        for r in arch.get("rights_restrictions") or []
    ]
    return {
        "focus_accession_id": focus,
        "as_of_date": arch["as_of_date"],
        "objects": objects,
        "transfers": transfers,
        "loans": loans,
        "restorations": restorations,
        "rights": rights,
    }


def _custody_lineage(transfers: list[dict[str, Any]], focus: str) -> list[str]:
    rows = [t for t in transfers if t["accession_id"] == focus]
    rows.sort(key=lambda t: t["transfer_date"])
    if not rows:
        return []
    out = [rows[0]["from_party"]]
    for t in rows:
        out.append(t["to_party"])
    return out


def _loan_conflicts(loans: list[dict[str, Any]], focus: str, as_of: str) -> list[dict[str, str]]:
    focus_loans = [loan for loan in loans if loan["accession_id"] == focus]
    focus_loans.sort(
        key=lambda loan: (
            loan["loan_start"],
            loan["loan_end"],
            loan["return_by"],
            loan["borrower"],
        )
    )
    out: list[dict[str, str]] = []
    for loan in focus_loans:
        if loan["return_by"] < as_of:
            out.append({"accession_id": focus, "reason": "missed_return_window"})
    for i, a in enumerate(focus_loans):
        for b in focus_loans[i + 1 :]:
            if a["loan_start"] <= b["loan_end"] and b["loan_start"] <= a["loan_end"]:
                out.append({"accession_id": focus, "reason": "overlapping_loan"})
    return out


def _active_restrictions(rights: list[dict[str, Any]], focus: str, as_of: str) -> list[dict[str, Any]]:
    by_level: dict[str, dict[str, Any]] = {}
    for r in rights:
        if r["accession_id"] != focus or r["expires"] < as_of:
            continue
        cur = by_level.get(r["level"])
        if cur is None or r["precedence"] < cur["precedence"]:
            by_level[r["level"]] = {"level": r["level"], "precedence": r["precedence"]}
    return sorted(by_level.values(), key=lambda x: x["level"])


def _restoration_timeline(events: list[dict[str, Any]], focus: str) -> list[dict[str, Any]]:
    rows = [e for e in events if e["accession_id"] == focus]
    return sorted(rows, key=lambda e: (e["event_date"], e["technician"], e["notes"]))


def _duplicate_conflicts(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for o in objects:
        counts[o["accession_id"]] = counts.get(o["accession_id"], 0) + 1
    out = []
    for aid, n in sorted(counts.items()):
        if n >= 2:
            out.append({"primary_accession_id": aid, "shadow_accession_ids": [aid] * n})
    return out


def _audit_digest(summary: dict[str, Any], lineage: list[str]) -> str:
    chain_json = json.dumps(lineage, separators=(",", ":"))
    body = (
        "{"
        f'"custody_depth":{int(summary["custody_depth"])},'
        f'"duplicate_count":{int(summary["duplicate_count"])},'
        f'"lineage":{chain_json},'
        f'"loan_conflicts":{int(summary["loan_conflict_count"])}'
        "}"
    )
    return hashlib.sha256(body.encode()).hexdigest()


def materialize_archive(path: Path, seed: str) -> dict[str, Any]:
    arch = json.loads(path.read_text(encoding="utf-8"))
    mat = _materialize(arch, seed)
    arch["_focus"] = mat["focus_accession_id"]
    arch["_materialized"] = mat
    return arch


def compute_aligned_dossier(arch: dict[str, Any], seed: str) -> dict[str, Any]:
    mat = arch["_materialized"]
    focus = mat["focus_accession_id"]
    lineage = _custody_lineage(mat["transfers"], focus)
    restrictions = _active_restrictions(mat["rights"], focus, mat["as_of_date"])
    timeline = _restoration_timeline(mat["restorations"], focus)
    loan_conflicts = _loan_conflicts(mat["loans"], focus, mat["as_of_date"])
    dupes = _duplicate_conflicts(mat["objects"])
    summary = {
        "custody_depth": len(lineage),
        "restriction_count": len(restrictions),
        "restoration_count": len(timeline),
        "loan_conflict_count": len(loan_conflicts),
        "duplicate_count": len(dupes),
    }
    return {
        "custody_lineage": lineage,
        "active_restrictions": restrictions,
        "restoration_timeline": timeline,
        "loan_conflicts": loan_conflicts,
        "duplicate_conflicts": dupes,
        "summary": summary,
    }


def compose_published_dossier(seed: str, archive: str, arch: dict[str, Any], aligned: dict[str, Any]) -> dict[str, Any]:
    summary = aligned["summary"]
    rep = {
        "seed": seed,
        "archive": archive,
        "focus_accession_id": arch["_focus"],
        "custody_lineage": aligned["custody_lineage"],
        "active_restrictions": aligned["active_restrictions"],
        "restoration_timeline": aligned["restoration_timeline"],
        "loan_conflicts": aligned["loan_conflicts"],
        "duplicate_conflicts": aligned["duplicate_conflicts"],
        "conflict_count": len(aligned["loan_conflicts"]) + len(aligned["duplicate_conflicts"]),
        "summary": summary,
    }
    rep["audit_digest"] = _audit_digest(summary, aligned["custody_lineage"])
    return rep


# Probe-visible aliases (first-submit / auto-probes scan for reference_*).
reference_load_archive = materialize_archive
reference_align = compute_aligned_dossier
reference_dossier = compose_published_dossier
