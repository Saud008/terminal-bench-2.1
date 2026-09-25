"""G-026 formulatrix load-scenario contract entry (pharmacy roster smoke)."""

from __future__ import annotations

import json
import subprocess

from formulatrix_refmath import normalize_ndc, reference_roster
from formulatrix_runner import FX_BIN, FX_BUNDLE, FX_ROSTER, fx_clean_state, fx_invoke


def test_t7cae68_formulary_load_populates_drug_roster() -> None:
    """load-scenario stores the drug roster with expected cardinality."""
    fx_clean_state()
    proc = fx_invoke(
        [FX_BIN, "load-scenario", "--scenario", "ndc-normalize", "--fixture-dir", str(FX_BUNDLE)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert isinstance(proc, subprocess.CompletedProcess)
    body = json.loads(FX_ROSTER.read_text(encoding="utf-8"))
    ref = reference_roster("ndc-normalize", FX_BUNDLE)
    assert len(body["drugs"]) == len(ref["drugs"])


def test_t7cae68_formulary_load_ndc_segment_format() -> None:
    """Roster NDC values pad to the 5-4-2 eleven-digit form."""
    fx_clean_state()
    fx_invoke([FX_BIN, "load-scenario", "--scenario", "ndc-normalize", "--fixture-dir", str(FX_BUNDLE)])
    body = json.loads(FX_ROSTER.read_text(encoding="utf-8"))
    raw = body["drugs"][0]["ndc"]
    assert normalize_ndc(raw) == "00012-3456-78"


def test_t7cae68_formulary_roster_lists_plan_ids() -> None:
    """Multi-plan roster preserves fixture plan_id membership."""
    fx_clean_state()
    fx_invoke([FX_BIN, "load-scenario", "--scenario", "multi-plan", "--fixture-dir", str(FX_BUNDLE)])
    body = json.loads(FX_ROSTER.read_text(encoding="utf-8"))
    fixture = json.loads((FX_BUNDLE / "scenarios/multi-plan/scenario.json").read_text(encoding="utf-8"))
    assert sorted(p["plan_id"] for p in body["plans"]) == sorted(p["plan_id"] for p in fixture["plans"])
    assert len(body["plans"]) == 2
