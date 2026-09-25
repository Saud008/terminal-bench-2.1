from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_manifest(manifest: str, fixture_root: Path) -> dict:
    path = fixture_root / "manifests" / f"{manifest}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_hs(raw: str) -> str:
    cleaned = raw.replace(".", "").replace("-", "").replace(" ", "")
    if len(cleaned) > 10:
        cleaned = cleaned[:10]
    while len(cleaned) < 10:
        cleaned += "0"
    return cleaned


def regional_value_bps(origin: str, shares: list[dict]) -> int:
    return sum(int(s["share_bps"]) for s in shares if s["country"] == origin)


def certificate_valid(shipment_date: str, issued_on: str, expires_on: str) -> bool:
    return issued_on <= shipment_date <= expires_on


def pick_agreement(hs_norm: str, rules: list[dict]) -> dict | None:
    matches = [r for r in rules if hs_norm.startswith(r["hs_prefix"])]
    if not matches:
        return None
    matches.sort(key=lambda r: (int(r["priority"]), r["agreement_code"]))
    return matches[0]


def reference_classifications(
    manifest: str,
    fixture_root: Path,
    rvc_floor_override: int | None = None,
) -> dict:
    sc = load_manifest(manifest, fixture_root)
    ship_date = sc["shipment_date"]
    certs = {c["line_id"]: c for c in sc.get("certificates", [])}
    rules = sc["agreement_rules"]
    lines_out: list[dict] = []
    for ln in sorted(sc["lines"], key=lambda x: x["line_id"]):
        hs = normalize_hs(ln["hs_raw"])
        rvc = regional_value_bps(ln["declared_origin"], ln["bom_shares"])
        rule = pick_agreement(hs, rules)
        treatment = "mfn"
        agree = "MFN"
        duty = 500
        cert_ok = False
        if rule is not None:
            agree = rule["agreement_code"]
            duty = int(rule["duty_rate_bps"])
            cert = certs.get(ln["line_id"])
            if cert is not None:
                cert_ok = certificate_valid(ship_date, cert["issued_on"], cert["expires_on"])
            min_bps = int(rule["rvc_min_bps"])
            if rvc_floor_override is not None and agree != "MFN":
                min_bps = rvc_floor_override
            if cert_ok and rvc >= min_bps and agree != "MFN":
                treatment = "preferential"
        lines_out.append(
            {
                "line_id": ln["line_id"],
                "hs_normalized": hs,
                "tariff_treatment": treatment,
                "agreement_code": agree,
                "rvc_bps": rvc,
                "cert_valid": cert_ok,
                "duty_rate_bps": duty,
            }
        )
    digest = hashlib.sha256(
        json.dumps(lines_out, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "scenario_id": sc["scenario_id"],
        "parse_pass": 1,
        "classifications": lines_out,
        "audit_digest": digest,
    }
