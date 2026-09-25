"""Independent crossmatch specification for blood-bank release ledger tests."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

RECIPIENT_ABO_RULES = {
    "O": frozenset({"O"}),
    "A": frozenset({"A", "O"}),
    "B": frozenset({"B", "O"}),
    "AB": frozenset({"A", "B", "AB", "O"}),
}

PANEL_TO_ANTIGEN = {
    "anti-D": "D",
    "anti-E": "E",
    "anti-C": "C",
    "anti-K": "K",
}


def read_scenario_bundle(scenario: str, fixture_root: Path) -> dict:
    raw = json.loads((fixture_root / "scenarios" / f"{scenario}.json").read_text(encoding="utf-8"))
    clock = os.environ.get("TB3_RELEASE_CLOCK")
    if clock:
        raw = dict(raw)
        raw["release_clock"] = clock
    return raw


def recipient_accepts_donor_abo(recipient: str, donor: str) -> bool:
    return donor in RECIPIENT_ABO_RULES.get(recipient, frozenset())


def rh_neg_constraint(patient_rh: str, unit_rh: str) -> bool:
    if patient_rh == "neg":
        return unit_rh == "neg"
    return unit_rh in {"pos", "neg"}


def immuno_conflict(screen: list[str], antigens: list[str]) -> bool:
    present = set(antigens)
    for marker in screen:
        mapped = PANEL_TO_ANTIGEN.get(marker)
        if mapped and mapped in present:
            return True
    return False


def shelf_elapsed(release_clock: str, expires_at: str) -> bool:
    return release_clock >= expires_at


def waiver_row(bundle: dict, patient_id: str, unit_id: str) -> dict | None:
    for row in bundle.get("overrides", []):
        if row["patient_id"] == patient_id and row["unit_id"] == unit_id:
            return row
    return None


def spec_crossmatch_rows(scenario: str, fixture_root: Path) -> list[dict]:
    bundle = read_scenario_bundle(scenario, fixture_root)
    patients = sorted(bundle["patients"], key=lambda p: p["patient_id"])
    units = sorted(bundle["units"], key=lambda u: (u["collected_at"], u["unit_id"]))
    rows: list[dict] = []
    for patient in patients:
        for unit in units:
            codes: list[str] = []
            ok = True
            if not recipient_accepts_donor_abo(patient["abo"], unit["abo"]):
                ok = False
                codes.append("abo_mismatch")
            if not rh_neg_constraint(patient["rh"], unit["rh"]):
                if waiver_row(bundle, patient["patient_id"], unit["unit_id"]) is None:
                    ok = False
                    codes.append("rh_mismatch")
            if immuno_conflict(patient.get("antibodies", []), unit.get("antigens", [])):
                ok = False
                codes.append("antibody_conflict")
            if shelf_elapsed(bundle["release_clock"], unit["expires_at"]):
                ok = False
                codes.append("unit_expired")
            rows.append(
                {
                    "patient_id": patient["patient_id"],
                    "unit_id": unit["unit_id"],
                    "compatible": ok,
                    "failure_codes": codes,
                }
            )
    rows.sort(key=lambda r: (r["patient_id"], r["unit_id"]))
    return rows


def spec_release_report(scenario: str, fixture_root: Path) -> dict:
    bundle = read_scenario_bundle(scenario, fixture_root)
    matrix = spec_crossmatch_rows(scenario, fixture_root)
    by_patient: dict[str, list[dict]] = {}
    for row in matrix:
        by_patient.setdefault(row["patient_id"], []).append(row)
    releases: list[dict] = []
    unit_order = {u["unit_id"]: u for u in sorted(bundle["units"], key=lambda u: (u["collected_at"], u["unit_id"]))}
    for patient in sorted(bundle["patients"], key=lambda p: p["patient_id"]):
        pid = patient["patient_id"]
        ordered = sorted(
            by_patient.get(pid, []),
            key=lambda r: (unit_order[r["unit_id"]]["collected_at"], r["unit_id"]),
        )
        for row in ordered:
            if not row["compatible"]:
                continue
            waiver = waiver_row(bundle, pid, row["unit_id"])
            releases.append(
                {
                    "patient_id": pid,
                    "unit_id": row["unit_id"],
                    "release_status": "approved",
                    "override_applied": waiver is not None,
                    "authorizer": waiver["authorizer"] if waiver else "",
                    "reason": waiver["reason"] if waiver else "",
                }
            )
            break
    releases.sort(key=lambda r: (r["patient_id"], r["unit_id"]))
    digest = hashlib.sha256(json.dumps(releases, separators=(",", ":")).encode()).hexdigest()
    return {
        "scenario_id": bundle["scenario_id"],
        "screening_pass": 1,
        "releases": releases,
        "ledger_digest": digest,
    }


# Back-compat aliases for contract tests
reference_crossmatch = spec_crossmatch_rows
reference_releases = spec_release_report
