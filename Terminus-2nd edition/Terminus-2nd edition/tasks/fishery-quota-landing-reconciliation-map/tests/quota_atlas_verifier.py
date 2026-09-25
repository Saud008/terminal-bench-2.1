"""Quota atlas verifier contract — fqrctl subprocess driver and contract math."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

APP = Path("/app")
BIN = APP / "bin" / "fqrctl"
FIXTURES = APP / "fixtures" / "seasons"
HIDDEN_TRAP_ROOT = "/opt/verifier-fixtures/fqr"
HIDDEN_ALIAS_TRAP = "/opt/verifier-fixtures/fqr/alias-mix-trap"


def fixture_root() -> Path:
    override = os.environ.get("FQR_FIXTURE_ROOT")
    return Path(override) if override else FIXTURES


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def rebuild_fqrctl() -> None:
    run(["bash", str(APP / "scripts" / "rebuild-fqrctl.sh")])


def reset_var() -> None:
    run(["bash", str(APP / "scripts" / "reset-var.sh")])


def emit_atlas(season: str, token: str, dest: Path | None = None) -> Path:
    dest = dest or APP / "output" / f"{token}.json"
    reset_var()
    rebuild_fqrctl()
    run([str(BIN), "--season", season, "--token", token, "--dest", str(dest)])
    return dest


def read_ledger_header(token: str) -> dict:
    path = APP / "var" / f"quota-ledger-{token}.header.json"
    return json.loads(path.read_text(encoding="utf-8"))


def species_rows_close(got: list[dict[str, Any]], want: list[dict[str, Any]]) -> None:
    assert len(got) == len(want)
    for g, w in zip(got, want):
        assert g["species"] == w["species"]
        for key in ("allocated_kg", "landed_kg", "remaining_kg", "over_quota_kg"):
            assert abs(float(g[key]) - float(w[key])) < 0.02


def audit_rows_close(got: list[dict[str, Any]], want: list[dict[str, Any]]) -> None:
    assert len(got) == len(want)
    for g, w in zip(got, want):
        assert g["landing_id"] == w["landing_id"]
        assert g["accepted"] == w["accepted"]
        assert g["reject_reason"] == w["reject_reason"]
        assert abs(float(g["live_weight_kg"]) - float(w["live_weight_kg"])) < 0.02


def round2(v: float) -> float:
    return round(v + 0.0, 2)


def reference_resolve_species(code: str, aliases: dict[str, list[str]]) -> str:
    upper = code.strip().upper()
    for lexicon_key, alts in aliases.items():
        if lexicon_key.upper() == upper:
            return lexicon_key
        for alt in alts:
            if alt.upper() == upper:
                return lexicon_key
    return upper


def reference_live_kg(product_kg: float, factor: float) -> float:
    return round2(product_kg * factor)


def reference_permit_covers(landed_at: str, valid_from: str, valid_until: str) -> bool:
    landed = landed_at[:10]
    return valid_from <= landed <= valid_until


def reference_species_permitted(species: str, allowed: list[str]) -> bool:
    return any(species.upper() == s.upper() for s in allowed)


def reference_closure_block(lat: float, lon: float, landed_at: str, area: dict[str, Any]) -> bool:
    landed = landed_at[:10]
    if landed < area["closed_from"] or landed > area["closed_until"]:
        return False
    return (
        area["min_lat"] <= lat <= area["max_lat"]
        and area["min_lon"] <= lon <= area["max_lon"]
    )


def reference_allocation(quota_kg: float, carryover_kg: float) -> float:
    return quota_kg + carryover_kg


def reference_materialize_rows(meta: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for landing in meta["landings"]:
        species = reference_resolve_species(landing["species_code"], meta["species_aliases"])
        factor = float(meta["conversion_factors"].get(species, 1.0))
        live = reference_live_kg(float(landing["product_weight_kg"]), factor)
        accepted = True
        reject_reason = ""
        permit = meta["permits"].get(landing["vessel_id"])
        if permit is None:
            accepted = False
            reject_reason = "missing_permit"
        elif not reference_permit_covers(landing["landed_at"], permit["valid_from"], permit["valid_until"]):
            accepted = False
            reject_reason = "permit_expired"
        elif not reference_species_permitted(species, permit["species"]):
            accepted = False
            reject_reason = "species_not_permitted"
        if accepted:
            for area in meta.get("closed_areas", []):
                if reference_closure_block(
                    float(landing["lat"]),
                    float(landing["lon"]),
                    landing["landed_at"],
                    area,
                ):
                    accepted = False
                    reject_reason = f"closed_area:{area['area_id']}"
                    break
        rows.append(
            {
                "landing_id": landing["landing_id"],
                "vessel_id": landing["vessel_id"],
                "species_raw": landing["species_code"],
                "species_resolved": species,
                "product_weight_kg": float(landing["product_weight_kg"]),
                "live_weight_kg": live,
                "landed_at": landing["landed_at"],
                "accepted": accepted,
                "reject_reason": reject_reason,
            }
        )
    rows.sort(key=lambda r: r["landing_id"])
    return rows


def reference_quota_atlas(token: str, meta: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    landed_by: dict[str, float] = {}
    for row in rows:
        if not row["accepted"]:
            continue
        species = row["species_resolved"]
        landed_by[species] = landed_by.get(species, 0.0) + float(row["live_weight_kg"])

    species_rows: list[dict[str, Any]] = []
    for species in sorted(meta["quota_kg"].keys()):
        quota = float(meta["quota_kg"][species])
        carry = float(meta["carryover_kg"].get(species, 0.0))
        allocated = round2(reference_allocation(quota, carry))
        landed = round2(landed_by.get(species, 0.0))
        species_rows.append(
            {
                "species": species,
                "allocated_kg": allocated,
                "landed_kg": landed,
                "remaining_kg": round2(max(0.0, allocated - landed)),
                "over_quota_kg": round2(max(0.0, landed - allocated)),
            }
        )

    landing_audit = [
        {
            "landing_id": r["landing_id"],
            "species": r["species_resolved"],
            "live_weight_kg": r["live_weight_kg"],
            "accepted": r["accepted"],
            "reject_reason": r["reject_reason"],
        }
        for r in sorted(rows, key=lambda x: x["landing_id"])
    ]
    accepted_count = sum(1 for r in landing_audit if r["accepted"])
    digest_body = {"species_rows": species_rows, "landing_audit": landing_audit}
    atlas_fingerprint = hashlib.sha256(json.dumps(digest_body, separators=(",", ":")).encode()).hexdigest()
    return {
        "run_token": token,
        "season": meta["season"],
        "species_rows": species_rows,
        "landing_audit": landing_audit,
        "summary": {"accepted_rows": accepted_count, "species_tracks": len(species_rows)},
        "atlas_fingerprint": atlas_fingerprint,
    }


def reference_atlas_from_season(season_dir: Path, token: str) -> dict[str, Any]:
    meta = json.loads((season_dir / "season.json").read_text(encoding="utf-8"))
    rows = reference_materialize_rows(meta)
    return reference_quota_atlas(token, meta, rows)
