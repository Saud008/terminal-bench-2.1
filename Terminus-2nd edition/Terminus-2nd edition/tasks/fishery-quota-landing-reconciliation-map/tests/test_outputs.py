"""Bundled fqrctl quota atlas contract tests for fishery landing reconciliation.

Verifier covers landing ingest bind, JSONL harvest snapshot, and quota atlas export paths.
"""

from __future__ import annotations

import json
from pathlib import Path

from quota_atlas_verifier import (
    audit_rows_close,
    emit_atlas,
    fixture_root,
    read_ledger_header,
    rebuild_fqrctl,
    reference_allocation,
    reference_atlas_from_season,
    reference_closure_block,
    reference_live_kg,
    reference_permit_covers,
    reference_resolve_species,
    reset_var,
    species_rows_close,
)

VAR_LEDGER = "/app/var/quota-ledger-{token}.jsonl"
OUTPUT_PREFIX = "/app/output/"



def test_t0ead00_fql7_twin_vessel_atlas_rows():
    """Twin-vessel season atlas species rows match independent reference math."""
    out = emit_atlas("twin-vessel-basic", "tok-twin")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas_from_season(fixture_root() / "twin-vessel-basic", "tok-twin")
    species_rows_close(rep["species_rows"], ref["species_rows"])


def test_t0ead00_fql7_harvest_ledger_snapshot():
    """Emit pass writes JSONL harvest ledger snapshot under /app/var/quota-ledger."""
    emit_atlas("twin-vessel-basic", "tok-stg")
    hdr = read_ledger_header("tok-stg")
    assert hdr["row_count"] == 2
    lines = Path(VAR_LEDGER.format(token="tok-stg")).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_t0ead00_fql7_jsonl_header_fingerprint():
    """Emit pass writes JSONL header with run_token and ledger_fingerprint."""
    emit_atlas("twin-vessel-basic", "tok-hdr")
    hdr = read_ledger_header("tok-hdr")
    assert hdr["run_token"] == "tok-hdr"
    assert "ledger_fingerprint" in hdr
    assert hdr["row_count"] == 2


def test_t0ead00_fql7_jsonl_path_exists():
    """Quota ledger JSONL exists under /app/var/quota-ledger after emit pass."""
    emit_atlas("twin-vessel-basic", "tok-jl")
    assert Path(VAR_LEDGER.format(token="tok-jl")).is_file()


def test_t0ead00_fql7_atlas_dest_under_output():
    """Emit pass writes caller dest under /app/output/ quota atlas path."""
    dest = Path(f"{OUTPUT_PREFIX}tok-out.json")
    out = emit_atlas("twin-vessel-basic", "tok-out", dest=dest)
    assert str(out).startswith(OUTPUT_PREFIX)
    assert out.is_file()


def test_t0ead00_fql7_species_alias_lexicon():
    """Regional species aliases resolve before conversion per species-alias-lexicon."""
    out = emit_atlas("species-alias-trap", "tok-alias")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas_from_season(fixture_root() / "species-alias-trap", "tok-alias")
    species_rows_close(rep["species_rows"], ref["species_rows"])


def test_t0ead00_fql7_live_weight_multiplier():
    """Live-weight conversion multiplies product weight per live-weight-conversion."""
    out = emit_atlas("weight-factor-trap", "tok-wgt")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas_from_season(fixture_root() / "weight-factor-trap", "tok-wgt")
    species_rows_close(rep["species_rows"], ref["species_rows"])


def test_t0ead00_fql7_permit_until_inclusive():
    """Permit validity includes landings on valid_until per permit-validity-window."""
    out = emit_atlas("permit-window-trap", "tok-prm")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas_from_season(fixture_root() / "permit-window-trap", "tok-prm")
    audit_rows_close(rep["landing_audit"], ref["landing_audit"])


def test_t0ead00_fql7_closed_area_polygon():
    """Closed-area contract rejects nursery landings inside bbox during closure dates."""
    out = emit_atlas("closed-area-trap", "tok-clo")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas_from_season(fixture_root() / "closed-area-trap", "tok-clo")
    audit_rows_close(rep["landing_audit"], ref["landing_audit"])
    species_rows_close(rep["species_rows"], ref["species_rows"])


def test_t0ead00_fql7_carryover_pool():
    """Carryover kilograms add to allocated quota per quota-carryover-pool."""
    out = emit_atlas("carryover-pool", "tok-car")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas_from_season(fixture_root() / "carryover-pool", "tok-car")
    species_rows_close(rep["species_rows"], ref["species_rows"])


def test_t0ead00_fql7_species_rows_sorted():
    """Atlas species rows sorted by species code ascending."""
    out = emit_atlas("twin-vessel-basic", "tok-srt")
    codes = [r["species"] for r in json.loads(out.read_text())["species_rows"]]
    assert codes == sorted(codes)


def test_t0ead00_fql7_audit_rows_sorted():
    """Landing audit sorted by landing_id ascending."""
    out = emit_atlas("twin-vessel-basic", "tok-aud")
    ids = [r["landing_id"] for r in json.loads(out.read_text())["landing_audit"]]
    assert ids == sorted(ids)


def test_t0ead00_fql7_atlas_fingerprint_stable():
    """atlas_fingerprint stable across repeated publish for same season bind."""
    reset_var()
    fp1 = json.loads(emit_atlas("twin-vessel-basic", "tok-fp").read_text())["atlas_fingerprint"]
    reset_var()
    fp2 = json.loads(emit_atlas("twin-vessel-basic", "tok-fp").read_text())["atlas_fingerprint"]
    assert fp1 == fp2


def test_t0ead00_fql7_summary_accepted_rows():
    """summary accepted_rows equals accepted audit rows."""
    body = json.loads(emit_atlas("twin-vessel-basic", "tok-sum").read_text())
    accepted = sum(1 for r in body["landing_audit"] if r["accepted"])
    assert body["summary"]["accepted_rows"] == accepted


def test_t0ead00_fql7_math_resolve_alias():
    """Alias lexicon resolves GAD to COD."""
    assert reference_resolve_species("GAD", {"COD": ["GAD", "GADUS"]}) == "COD"


def test_t0ead00_fql7_math_live_conversion():
    """Product to live uses multiplier."""
    assert reference_live_kg(1000.0, 1.15) == 1150.0


def test_t0ead00_fql7_math_permit_inclusive_end():
    """Permit covers landing on valid_until date."""
    assert reference_permit_covers("2025-09-30T18:00:00Z", "2025-04-01", "2025-09-30")
    assert not reference_permit_covers("2025-10-01T08:00:00Z", "2025-04-01", "2025-09-30")


def test_t0ead00_fql7_math_carryover_addition():
    """Allocation equals quota plus carryover."""
    assert reference_allocation(4000.0, 500.0) == 4500.0


def test_t0ead00_fql7_math_closure_bbox():
    """Closure bbox detects inside points during closed window."""
    area = {
        "area_id": "NURSERY",
        "min_lat": 59.0,
        "max_lat": 60.0,
        "min_lon": 4.5,
        "max_lon": 5.5,
        "closed_from": "2025-05-01",
        "closed_until": "2025-10-31",
    }
    assert reference_closure_block(59.5, 5.0, "2025-07-20T14:00:00Z", area)
    assert not reference_closure_block(61.0, 6.5, "2025-07-21T10:00:00Z", area)


def test_t0ead00_fql7_fqrctl_subprocess_invocation():
    """Pytest invokes fqrctl through subprocess after rebuild."""
    out = emit_atlas("twin-vessel-basic", "tok-subproc")
    assert out.is_file()


def test_t0ead00_fql7_fqrctl_binary_installed():
    """rebuild-fqrctl installs /app/bin/fqrctl."""
    reset_var()
    rebuild_fqrctl()
    assert Path("/app/bin/fqrctl").is_file()


def test_t0ead00_fql7_remaining_when_under_quota():
    """remaining_kg plus landed_kg equals allocated when not over quota."""
    body = json.loads(emit_atlas("carryover-pool", "tok-bal").read_text())
    cod = next(r for r in body["species_rows"] if r["species"] == "COD")
    if cod["over_quota_kg"] == 0:
        assert abs(cod["remaining_kg"] + cod["landed_kg"] - cod["allocated_kg"]) < 0.05
