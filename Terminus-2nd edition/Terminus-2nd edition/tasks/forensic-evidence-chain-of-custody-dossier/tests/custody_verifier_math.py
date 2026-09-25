"""Independent custody dossier reference math."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def load_locations(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["location_id"]: row["status"] for row in data["locations"]}


def preserve_officer(officer_id: str) -> str:
    return officer_id


def build_edges(transfers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [t for t in transfers if t["event_type"] == "transfer"]
    rows.sort(key=lambda t: (t["evidence_id"], t["event_epoch_ms"], t["event_id"]))
    return [
        {
            "evidence_id": t["evidence_id"],
            "from_officer_id": preserve_officer(t["from_officer_id"]),
            "to_officer_id": preserve_officer(t["to_officer_id"]),
            "event_epoch_ms": t["event_epoch_ms"],
        }
        for t in rows
    ]


def seal_findings(transfers: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in transfers:
        if row["seal_number"] != row["expected_seal"]:
            out.append(
                {
                    "evidence_id": row["evidence_id"],
                    "code": "seal_break",
                    "detail": f"seal {row['seal_number']} expected {row['expected_seal']}",
                }
            )
    return out


def location_findings(
    transfers: list[dict[str, Any]], catalog: dict[str, str]
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in transfers:
        status = catalog.get(row["to_location_id"], "")
        if status != "active":
            out.append(
                {
                    "evidence_id": row["evidence_id"],
                    "code": "location_invalid",
                    "detail": row["to_location_id"],
                }
            )
    return out


def chrono_findings(transfers: list[dict[str, Any]]) -> list[dict[str, str]]:
    last: dict[str, int] = {}
    out: list[dict[str, str]] = []
    ordered = sorted(transfers, key=lambda t: (t["evidence_id"], t["event_epoch_ms"], t["event_id"]))
    for row in ordered:
        prev = last.get(row["evidence_id"])
        if prev is not None and row["event_epoch_ms"] <= prev:
            out.append(
                {
                    "evidence_id": row["evidence_id"],
                    "code": "chronology_violation",
                    "detail": f"{row['event_epoch_ms']} before {prev}",
                }
            )
        last[row["evidence_id"]] = row["event_epoch_ms"]
    return out


def lab_window_findings(transfers: list[dict[str, Any]]) -> list[dict[str, str]]:
    max_transfer: dict[str, int] = {}
    for row in transfers:
        if row["event_type"] == "transfer":
            eid = row["evidence_id"]
            max_transfer[eid] = max(max_transfer.get(eid, 0), row["event_epoch_ms"])
    out: list[dict[str, str]] = []
    for row in transfers:
        if row["event_type"] == "lab_submit":
            anchor = max_transfer.get(row["evidence_id"], 0)
            if row["event_epoch_ms"] <= anchor:
                out.append(
                    {
                        "evidence_id": row["evidence_id"],
                        "code": "chronology_violation",
                        "detail": "lab_submit before transfer",
                    }
                )
    return out


def alias_findings(aliases: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: dict[str, str] = {}
    out: list[dict[str, str]] = []
    for row in aliases:
        prior = seen.get(row["court_alias"])
        if prior is not None and prior != row["evidence_id"]:
            out.append(
                {
                    "evidence_id": row["evidence_id"],
                    "code": "alias_collision",
                    "detail": row["court_alias"],
                }
            )
        seen[row["court_alias"]] = row["evidence_id"]
    return out


def lineage_gap(evidence_id: str, transfers: list[dict[str, Any]]) -> bool:
    chain = [
        t
        for t in transfers
        if t["evidence_id"] == evidence_id and t["event_type"] == "transfer"
    ]
    chain.sort(key=lambda t: t["event_epoch_ms"])
    if len(chain) < 2:
        return False
    for left, right in zip(chain, chain[1:]):
        if left["to_officer_id"] != right["from_officer_id"]:
            return True
    return False


def reference_dossier(
    case_id: str,
    bundle_path: Path,
    catalog_path: Path,
    run_seq: int = 1,
) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    catalog = load_locations(catalog_path)
    transfers = bundle["transfers"] + bundle.get("seal_checks", [])
    normalized = []
    for row in transfers:
        item = dict(row)
        item["from_officer_id"] = preserve_officer(row["from_officer_id"])
        item["to_officer_id"] = preserve_officer(row["to_officer_id"])
        normalized.append(item)

    broken: list[dict[str, str]] = []
    broken.extend(seal_findings(normalized))
    broken.extend(location_findings(normalized, catalog))
    broken.extend(chrono_findings(normalized))
    broken.extend(lab_window_findings(normalized))
    broken.extend(alias_findings(bundle.get("exhibit_aliases", [])))

    evidence_items = sorted({t["evidence_id"] for t in normalized})
    for eid in evidence_items:
        if lineage_gap(eid, normalized):
            broken.append(
                {
                    "evidence_id": eid,
                    "code": "lineage_gap",
                    "detail": "custody hop discontinuity",
                }
            )

    broken.sort(key=lambda b: (b["evidence_id"], b["code"]))
    broken_ids = sorted({b["evidence_id"] for b in broken})

    def count(code: str) -> int:
        return sum(1 for b in broken if b["code"] == code)

    summary = {
        "intact_items": len(evidence_items) - len(broken_ids),
        "defect_items": len(broken_ids),
        "seal_breaks": count("seal_break"),
        "location_invalid": count("location_invalid"),
        "chronology_violation": count("chronology_violation"),
        "lineage_gap": count("lineage_gap"),
        "alias_collision": count("alias_collision"),
    }

    body = json.dumps(
        {
            "case_id": case_id,
            "bundle_id": bundle["bundle_id"],
            "run_seq": run_seq,
            "intact_items": summary["intact_items"],
            "defect_items": summary["defect_items"],
            "finding_ids": [f"{b['evidence_id']}:{b['code']}" for b in broken],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(body.encode()).hexdigest()

    return {
        "case_id": case_id,
        "bundle_id": bundle["bundle_id"],
        "run_seq": run_seq,
        "evidence_items": evidence_items,
        "lineage_edges": build_edges(normalized),
        "integrity_findings": broken,
        "summary": summary,
        "custody_digest": digest,
    }


def materialize_bundle(bundle_path: Path, seed: int) -> dict[str, Any]:
    """Randomize ids for anti-hardcoding without changing graph shape."""
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    salt = f"S{seed:04d}"
    for row in bundle["transfers"]:
        row["evidence_id"] = f"EVD-{salt}-{row['evidence_id'].split('-')[-1]}"
        row["from_officer_id"] = f"OFF-{salt}-{row['from_officer_id'].split('-')[-1]}"
        row["to_officer_id"] = f"OFF-{salt}-{row['to_officer_id'].split('-')[-1]}"
        row["seal_number"] = f"SEAL-{salt}-{row['seal_number'].split('-')[-1]}"
        row["expected_seal"] = row["seal_number"]
    for alias in bundle.get("exhibit_aliases", []):
        alias["evidence_id"] = f"EVD-{salt}-{alias['evidence_id'].split('-')[-1]}"
        alias["court_alias"] = f"EXH-{salt}-{alias['court_alias'].split('-')[-1]}"
    bundle["case_id"] = f"CASE-RAND-{salt}"
    bundle["bundle_id"] = "rand-chain"
    return bundle
