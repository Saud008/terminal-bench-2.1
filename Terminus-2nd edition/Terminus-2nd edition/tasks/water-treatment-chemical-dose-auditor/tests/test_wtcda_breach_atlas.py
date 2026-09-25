"""Breach atlas field contract tests separate from bundled shift math."""

from __future__ import annotations

import json

from wtcda_refmath import reference_safety
from wtcda_subprocess import FIXTURE_DIR, run_safety_pipeline, wipe


def test_wtcda_p20() -> None:
    """safety-limit-report.md defines plant_id, shift, rows, summary, breach_atlas_seal."""
    wipe()
    plant, shift = "plant-south-epsilon", "turbidity-uplift-cap"
    out = run_safety_pipeline(plant, shift)
    body = json.loads(out.read_text(encoding="utf-8"))
    for key in ("plant_id", "shift", "rows", "summary", "breach_atlas_seal"):
        assert key in body


def test_wtcda_p21() -> None:
    """Each breach row includes chem_id, total_dose_mg, max_dose_mg, severity_pct."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    out = run_safety_pipeline(plant, shift)
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    for row in rows:
        for key in ("chem_id", "total_dose_mg", "max_dose_mg", "severity_pct"):
            assert key in row


def test_wtcda_p22() -> None:
    """breach_atlas_seal must match reference for identical ledger content."""
    wipe()
    plant, shift = "plant-west-delta", "override-role-mix"
    out = run_safety_pipeline(plant, shift)
    got = json.loads(out.read_text(encoding="utf-8"))
    exp = reference_safety(plant, shift, FIXTURE_DIR / f"{shift}.json")
    assert got["breach_atlas_seal"] == exp["breach_atlas_seal"]
