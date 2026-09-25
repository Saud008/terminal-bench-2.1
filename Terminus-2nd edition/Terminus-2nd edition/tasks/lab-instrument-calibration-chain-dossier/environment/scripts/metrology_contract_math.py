#!/usr/bin/env python3
"""Independent contract math for calbind calibration dossier verifier."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from pathlib import Path
from typing import Any

VAULT_PATH = Path("/app/state/intake-vault.json")
REGISTER_PATH = Path("/app/work/calibration-register.db")
COVERAGE = 2.0


def cert_digest(instrument_id: str, as_of_date: str, cert_id: str) -> str:
    body = f"{instrument_id}:{as_of_date}:{cert_id}".encode()
    return hashlib.sha256(body).hexdigest()[:16]


def cert_valid_on_date(expires: str, as_of: str) -> bool:
    return expires >= as_of


def trace_root(chain: list[dict[str, Any]]) -> str:
    for link in chain:
        if link.get("parent_std") is None:
            return link["std_id"]
    raise ValueError("no root")


def chain_complete(chain: list[dict[str, Any]]) -> bool:
    if not chain:
        return False
    prev_id: str | None = None
    for i, link in enumerate(chain):
        parent = link.get("parent_std")
        if i == 0:
            if parent is not None:
                return False
        elif parent != prev_id:
            return False
        prev_id = link["std_id"]
    return True


def combined_standard(components: list[dict[str, Any]]) -> float:
    return math.sqrt(sum(c["value"] ** 2 for c in components))


def expanded_uncertainty(combined: float, coverage_k: float = COVERAGE) -> float:
    return combined * coverage_k


def technician_authorized(tech: dict[str, Any], instrument_id: str, as_of: str) -> bool:
    if tech["qual_expires"] < as_of:
        return False
    return instrument_id in tech["scope_instruments"]


def channel_within(reading: dict[str, Any]) -> bool:
    value = reading["value"]
    nominal = reading["nominal"]
    return value <= nominal + reading["tol_plus"] and value >= nominal - reading["tol_minus"]


def channel_decisions(readings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "channel": r["channel"],
            "within_tolerance": channel_within(r),
            "deviation": abs(r["value"] - r["nominal"]),
        }
        for r in readings
    ]


def oot_count(readings: list[dict[str, Any]]) -> int:
    return sum(1 for r in readings if not channel_within(r))


def stage_from_pack(pack: dict[str, Any]) -> dict[str, Any]:
    combined = combined_standard(pack["uncertainty_budget"])
    return {
        "instrument_id": pack["instrument_id"],
        "cert_valid": cert_valid_on_date(pack["certificate"]["expires"], pack["as_of_date"]),
        "cert_digest": cert_digest(
            pack["instrument_id"], pack["as_of_date"], pack["certificate"]["cert_id"]
        ),
        "std_root": trace_root(pack["standard_chain"]),
        "combined_uncertainty": combined,
        "expanded_uncertainty": expanded_uncertainty(combined),
        "authorized_tech": technician_authorized(
            pack["technician"], pack["instrument_id"], pack["as_of_date"]
        ),
        "decisions": channel_decisions(pack["readings"]),
        "out_of_tolerance_count": oot_count(pack["readings"]),
    }


def dossier_row_severity(inst: dict[str, Any]) -> int:
    sev = inst["out_of_tolerance_count"] * 10
    if not inst["cert_valid"]:
        sev += 5
    if not inst["authorized_tech"]:
        sev += 3
    return sev


def contract_dossier(batch_id: str, inst: dict[str, Any], fuse_generation: int) -> dict[str, Any]:
    row = {
        "instrument_id": inst["instrument_id"],
        "severity": dossier_row_severity(inst),
        "out_of_tolerance_count": inst["out_of_tolerance_count"],
        "cert_valid": inst["cert_valid"],
        "authorized_tech": inst["authorized_tech"],
        "expanded_uncertainty": inst["expanded_uncertainty"],
    }
    rows = [row]
    summary = {
        "instrument_count": 1,
        "invalid_cert_count": 0 if inst["cert_valid"] else 1,
        "unauthorized_tech_count": 0 if inst["authorized_tech"] else 1,
        "oot_channel_total": inst["out_of_tolerance_count"],
    }
    parts = sorted(
        f"{r['instrument_id']}:{r['severity']}:{r['out_of_tolerance_count']}" for r in rows
    )
    body = (
        f"{batch_id}|{fuse_generation}|{summary['instrument_count']}|"
        f"{summary['invalid_cert_count']}|{summary['unauthorized_tech_count']}|{';'.join(parts)}"
    )
    digest = hashlib.sha256(body.encode()).hexdigest()[:16]
    return {
        "batch_id": batch_id,
        "fuse_generation": fuse_generation,
        "rows": rows,
        "summary": summary,
        "dossier_digest": digest,
    }


def read_register_payload(batch_id: str) -> dict[str, Any]:
    conn = sqlite3.connect(REGISTER_PATH)
    try:
        row = conn.execute(
            "SELECT payload_json FROM calibration_register WHERE batch_id = ?",
            (batch_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise KeyError(batch_id)
    return json.loads(row[0])


def read_fuse_generation(batch_id: str) -> int:
    conn = sqlite3.connect(REGISTER_PATH)
    try:
        row = conn.execute(
            "SELECT fuse_generation FROM calibration_register WHERE batch_id = ?",
            (batch_id,),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0]) if row else 0


def reference_dossier(batch_id: str, inst: dict[str, Any], fuse_generation: int) -> dict[str, Any]:
    return contract_dossier(batch_id, inst, fuse_generation)
