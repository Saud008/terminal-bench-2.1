"""Independent calloutd dispatch reference simulator."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def load_bundle(root: Path, scenario: str) -> dict:
    return json.loads((root / "scenarios" / scenario / "bundle.json").read_text(encoding="utf-8"))


def travel_buffer() -> int:
    raw = os.environ.get("TB3_TRAVEL_BUFFER", "")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return 15


def pick_sla(bundle: dict, building_id: str) -> dict:
    contracts = [c for c in bundle["sla_contracts"] if c["building_id"] == building_id]
    return max(contracts, key=lambda c: c["tier_rank"])


def score_fault(fault: dict, bundle: dict) -> dict:
    if fault.get("cancelled"):
        return {}
    sla = pick_sla(bundle, fault["building_id"])
    anchor = int(bundle["roster_epoch_minute"])
    breach = sla["max_response_minutes"] - (anchor - int(fault["reported_minute"]))
    urgency = 100 if breach < 0 else max(0, 100 - breach)
    priority = (
        int(fault["severity_base"]) * 100
        + int(fault["trapped_passengers"]) * 50
        + urgency * 10
        + int(sla["escalation_weight"])
    )
    return {
        "fault_id": fault["fault_id"],
        "priority_score": priority,
        "sla_urgency": urgency,
        "breach_horizon_min": breach,
    }


def reference_scores(fixture_root: Path, scenario: str) -> list[dict]:
    bundle = load_bundle(fixture_root, scenario)
    rows = []
    for fault in bundle["faults"]:
        row = score_fault(fault, bundle)
        if row:
            rows.append(row)
    rows.sort(key=lambda r: (-r["priority_score"], r["fault_id"]))
    return rows


def building_access(bundle: dict, building_id: str, planned: int) -> bool:
    for b in bundle["buildings"]:
        if b["building_id"] != building_id:
            continue
        for w in b["access_windows"]:
            if w["start_minute"] <= planned <= w["end_minute"]:
                return True
    return False


def reference_assignments(fixture_root: Path, scenario: str) -> list[dict]:
    bundle = load_bundle(fixture_root, scenario)
    travel = travel_buffer()
    if "travel_buffer_minutes" in bundle:
        travel = int(bundle["travel_buffer_minutes"])
    scores = {r["fault_id"]: r for r in reference_scores(fixture_root, scenario)}
    faults = [f for f in bundle["faults"] if not f.get("cancelled") and f["fault_id"] in scores]
    faults.sort(key=lambda f: (-scores[f["fault_id"]]["priority_score"], f["fault_id"]))
    techs = sorted(bundle["technicians"], key=lambda t: t["tech_id"])
    load: dict[str, int] = {}
    out: list[dict] = []
    for fault in faults:
        planned = int(fault["reported_minute"]) + travel
        candidates = []
        for tech in techs:
            if int(tech["skill_level"]) < int(fault["required_skill"]):
                continue
            if load.get(tech["tech_id"], 0) >= 2:
                continue
            if not (int(tech["shift_start"]) <= planned <= int(tech["shift_end"])):
                continue
            if not building_access(bundle, fault["building_id"], planned):
                continue
            candidates.append(tech)
        candidates.sort(key=lambda t: (load.get(t["tech_id"], 0), t["tech_id"]))
        if not candidates:
            continue
        pick = candidates[0]
        out.append(
            {
                "fault_id": fault["fault_id"],
                "tech_id": pick["tech_id"],
                "planned_minute": planned,
                "status": "locked",
            }
        )
        load[pick["tech_id"]] = load.get(pick["tech_id"], 0) + 1
    out.sort(key=lambda r: r["fault_id"])
    return out


def reference_roster(fixture_root: Path, scenario: str) -> dict:
    bundle = load_bundle(fixture_root, scenario)
    assignments = reference_assignments(fixture_root, scenario)
    scores = reference_scores(fixture_root, scenario)
    breach = {r["fault_id"]: r["breach_horizon_min"] for r in scores}
    digest = hashlib.sha256(
        json.dumps(assignments, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "scenario": scenario,
        "roster_epoch_minute": int(bundle["roster_epoch_minute"]),
        "assignments": assignments,
        "breach_horizon_summary": breach,
        "roster_digest": digest,
    }
