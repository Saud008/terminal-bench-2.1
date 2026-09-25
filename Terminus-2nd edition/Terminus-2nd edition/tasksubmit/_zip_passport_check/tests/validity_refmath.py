from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import date
from pathlib import Path

from validity_runner import derive_doc_id as seed_doc_id


def parse_day(value: str) -> date:
    return date.fromisoformat(value)


def days_inclusive(start: date, end: date) -> int:
    return (end - start).days + 1


def passport_valid_at(reference: str, issue: str, expiry: str) -> bool:
    ref = parse_day(reference)
    return parse_day(issue) <= ref <= parse_day(expiry)


def visa_contained(
    reference: str,
    valid_from: str,
    valid_to: str,
    passport_issue: str,
    passport_expiry: str,
) -> bool:
    ref = parse_day(reference)
    vf = parse_day(valid_from)
    vt = parse_day(valid_to)
    if ref < vf or ref > vt:
        return False
    return not (vf < parse_day(passport_issue) or vt > parse_day(passport_expiry))


def cumulative_stay_days(reference: str, stamps: list[dict], grace_days: int) -> int:
    ref = parse_day(reference)
    total = 0
    for st in stamps:
        entry = parse_day(st["entry_date"])
        if entry > ref:
            continue
        end = ref
        if st.get("exit_date"):
            exit_d = parse_day(st["exit_date"])
            if exit_d < ref:
                end = exit_d
        total += days_inclusive(entry, end)
    _ = grace_days
    return total


def effective_max_stay(port_code: str, rules: list[dict]) -> int:
    federal = 0
    port_cap = 0
    for rule in rules:
        if rule["scope"] == "federal":
            federal = max(federal, int(rule["max_stay_days"]))
        elif rule["scope"] == "port" and rule.get("port_code") == port_code:
            port_cap = max(port_cap, int(rule["max_stay_days"]))
    if federal > 0:
        return federal
    return port_cap


def latest_port(stamps: list[dict]) -> str:
    if not stamps:
        return ""
    return stamps[-1]["port_code"]


def document_active(doc_revoked: bool, passport_revoked: bool, is_visa: bool) -> bool:
    if doc_revoked:
        return False
    if is_visa and passport_revoked:
        return False
    return not (not is_visa and passport_revoked)


def has_blocking_hold(holder_id: str, holds: list[dict]) -> bool:
    return any(h["holder_id"] == holder_id and h.get("active") for h in holds)


def load_scenario(scenario: str, fixture_root: Path, seed: str | None = None) -> dict:
    raw = json.loads((fixture_root / "scenarios" / f"{scenario}.json").read_text(encoding="utf-8"))
    if not seed:
        return raw
    sc = deepcopy(raw)
    pass_map: dict[str, str] = {}
    for p in sc.get("passports", []):
        old = p["doc_id"]
        p["doc_id"] = seed_doc_id(old, seed)
        pass_map[old] = p["doc_id"]
    for v in sc.get("visas", []):
        v["doc_id"] = seed_doc_id(v["doc_id"], seed)
        v["passport_id"] = pass_map.get(v["passport_id"], v["passport_id"])
    for st in sc.get("stamps", []):
        st["stamp_id"] = seed_doc_id(st["stamp_id"], seed)
        st["passport_id"] = pass_map.get(st["passport_id"], st["passport_id"])
    return sc


def reference_decisions(
    scenario: str,
    fixture_root: Path,
    eval_pass: int = 1,
    seed: str | None = None,
) -> dict:
    sc = load_scenario(scenario, fixture_root, seed=seed)
    ref_date = sc["reference_date"]
    grace = int(sc.get("grace_days", 0))
    passports = {p["doc_id"]: p for p in sc["passports"]}
    stamps_by_pass: dict[str, list[dict]] = {}
    for st in sc.get("stamps", []):
        stamps_by_pass.setdefault(st["passport_id"], []).append(st)

    rows: list[dict] = []
    for visa in sc.get("visas", []):
        passport = passports[visa["passport_id"]]
        reasons: list[str] = []
        if not document_active(visa.get("revoked", False), passport.get("revoked", False), True):
            reasons.append("document_revoked")
        if not passport_valid_at(ref_date, passport["issue_date"], passport["expiry_date"]):
            reasons.append("passport_window")
        if not visa_contained(
            ref_date,
            visa["valid_from"],
            visa["valid_to"],
            passport["issue_date"],
            passport["expiry_date"],
        ):
            reasons.append("visa_overlap")
        if has_blocking_hold(passport["holder_id"], sc.get("holds", [])):
            reasons.append("watchlist_hold")

        port = latest_port(stamps_by_pass.get(passport["doc_id"], []))
        max_stay = effective_max_stay(port, sc.get("rules", []))
        cum = cumulative_stay_days(ref_date, stamps_by_pass.get(passport["doc_id"], []), grace)
        remaining = max(0, max_stay - cum)
        if max_stay > 0 and cum > max_stay + grace:
            reasons.append("stay_exceeded")

        rows.append(
            {
                "holder_id": passport["holder_id"],
                "passport_id": passport["doc_id"],
                "visa_id": visa["doc_id"],
                "allowed_entry": len(reasons) == 0,
                "deny_reasons": reasons,
                "cumulative_stay_days": cum,
                "max_stay_allowed": max_stay,
                "remaining_stay_days": remaining,
            }
        )

    rows.sort(key=lambda r: (r["holder_id"], r["visa_id"]))
    digest = hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()
    return {
        "scenario_id": sc["scenario_id"],
        "eval_pass": eval_pass,
        "reference_date": ref_date,
        "decisions": rows,
        "ledger_digest": digest,
    }
