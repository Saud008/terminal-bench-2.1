"""Independent formulary coverage refmath for formulatrix verifier."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def load_scenario(fixture_root: Path, scenario: str) -> dict[str, Any]:
    path = fixture_root / "scenarios" / scenario / "scenario.json"
    return json.loads(path.read_text(encoding="utf-8"))


def as_of_date(doc: dict[str, Any]) -> str:
    override = os.environ.get("TB3_AS_OF_DATE", "")
    return override or str(doc.get("as_of", "2024-06-15"))


def normalize_ndc(raw: str) -> str:
    digits = raw.replace("-", "")
    digits = digits.zfill(11)
    return f"{digits[:5]}-{digits[5:9]}-{digits[9:11]}"


def preferred_rxnorm(drug: dict[str, Any]) -> str:
    if drug.get("rxnorm"):
        return str(drug["rxnorm"])
    aliases = list(drug.get("aliases") or [])
    if not aliases:
        return ""
    best_rank = max(int(a["rank"]) for a in aliases)
    top = [a for a in aliases if int(a["rank"]) == best_rank]
    top.sort(key=lambda a: str(a["code"]))
    return str(top[0]["code"])


def date_active(start: str, end: str, as_of: str) -> bool:
    if as_of < start:
        return False
    return not (end and as_of > end)


def select_override(rules: list[dict[str, Any]], plan_id: str, ndc: str, as_of: str) -> dict[str, Any] | None:
    active = [
        r
        for r in rules
        if r["plan_id"] == plan_id and r["ndc"] == ndc and date_active(r["effective_start"], r.get("effective_end", ""), as_of)
    ]
    if not active:
        return None
    best_priority = max(int(r["priority"]) for r in active)
    tier = [r for r in active if int(r["priority"]) == best_priority]
    tier.sort(key=lambda r: r["effective_start"], reverse=True)
    return tier[0]


def step_complete(links: list[dict[str, Any]], plan_id: str, target_ndc: str, pa_by_ndc: dict[str, bool]) -> bool:
    chain = [lnk for lnk in links if lnk["plan_id"] == plan_id and lnk["target_ndc"] == target_ndc]
    chain.sort(key=lambda lnk: int(lnk["sequence"]))
    for link in chain:
        prereq = normalize_ndc(str(link["prerequisite_ndc"]))
        if pa_by_ndc.get(prereq, True):
            return False
    return True


def _digest_bytes(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def _drug_digest(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "ndc": d["ndc"],
        "rxnorm": d.get("rxnorm", ""),
        "name": d.get("name", ""),
        "aliases": [{"code": a["code"], "rank": int(a["rank"])} for a in (d.get("aliases") or [])],
    }


def _override_digest(o: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_id": o["plan_id"],
        "ndc": o["ndc"],
        "pa_required": bool(o["pa_required"]),
        "priority": int(o["priority"]),
        "effective_start": o["effective_start"],
        "effective_end": o.get("effective_end", ""),
    }


def _plan_digest(p: dict[str, Any]) -> dict[str, Any]:
    return {"plan_id": p["plan_id"], "name": p.get("name", "")}


def _step_digest(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_id": s["plan_id"],
        "target_ndc": s["target_ndc"],
        "prerequisite_ndc": s["prerequisite_ndc"],
        "sequence": int(s["sequence"]),
    }


def _row_digest(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_id": r["plan_id"],
        "ndc_normalized": r["ndc_normalized"],
        "preferred_rxnorm": r["preferred_rxnorm"],
        "requires_pa": bool(r["requires_pa"]),
        "step_complete": bool(r["step_complete"]),
        "override_applied": bool(r["override_applied"]),
        "effective_rule": r["effective_rule"],
    }


def reference_roster(scenario: str, fixture_root: Path) -> dict[str, Any]:
    doc = load_scenario(fixture_root, scenario)
    drugs = sorted(doc["drugs"], key=lambda d: normalize_ndc(str(d["ndc"])))
    payload = {
        "as_of": as_of_date(doc),
        "drugs": [_drug_digest(d) for d in drugs],
        "overrides": [_override_digest(o) for o in doc.get("overrides", [])],
        "plans": [_plan_digest(p) for p in doc.get("plans", [])],
        "scenario": scenario,
        "step_chains": [_step_digest(s) for s in doc.get("step_chains", [])],
    }
    digest = _digest_bytes(payload)
    return {
        "engine": "formulatrix",
        "scenario": scenario,
        "as_of": payload["as_of"],
        "drugs": doc["drugs"],
        "plans": doc["plans"],
        "overrides": doc.get("overrides", []),
        "step_chains": doc.get("step_chains", []),
        "roster_digest": digest,
    }


def reference_matrix(scenario: str, fixture_root: Path) -> dict[str, Any]:
    doc = load_scenario(fixture_root, scenario)
    as_of = as_of_date(doc)
    rows: list[dict[str, Any]] = []
    for plan in doc["plans"]:
        plan_id = str(plan["plan_id"])
        pa_by_ndc: dict[str, bool] = {normalize_ndc(str(d["ndc"])): True for d in doc["drugs"]}
        for drug in doc["drugs"]:
            raw_ndc = str(drug["ndc"])
            ndc = normalize_ndc(raw_ndc)
            ovr = select_override(doc.get("overrides", []), plan_id, raw_ndc, as_of)
            if ovr is not None:
                pa_by_ndc[ndc] = bool(ovr["pa_required"])
        for drug in doc["drugs"]:
            raw_ndc = str(drug["ndc"])
            ndc = normalize_ndc(raw_ndc)
            rx = preferred_rxnorm(drug)
            requires_pa = pa_by_ndc[ndc]
            override_applied = False
            effective_rule = "baseline"
            ovr = select_override(doc.get("overrides", []), plan_id, raw_ndc, as_of)
            if ovr is not None:
                requires_pa = bool(ovr["pa_required"])
                override_applied = True
                effective_rule = str(ovr["effective_start"])
            step_ok = step_complete(doc.get("step_chains", []), plan_id, raw_ndc, pa_by_ndc)
            rows.append(
                {
                    "plan_id": plan_id,
                    "ndc_normalized": ndc,
                    "preferred_rxnorm": rx,
                    "requires_pa": requires_pa,
                    "step_complete": step_ok,
                    "override_applied": override_applied,
                    "effective_rule": effective_rule,
                }
            )
    rows.sort(key=lambda r: (r["plan_id"], r["ndc_normalized"]))
    payload = {
        "as_of": as_of,
        "row_count": len(rows),
        "rows": [_row_digest(r) for r in rows],
        "scenario": scenario,
    }
    publish = {
        "scenario": scenario,
        "as_of": as_of,
        "row_count": len(rows),
        "rows": rows,
        "matrix_digest": _digest_bytes(payload),
    }
    return publish
