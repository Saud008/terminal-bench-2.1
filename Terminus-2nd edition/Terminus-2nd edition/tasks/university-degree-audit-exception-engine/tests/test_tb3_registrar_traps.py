"""Hidden verifier trap scenarios for catalog year and substitution expiry boundaries."""

from __future__ import annotations

import json

from registrar_graph_sim import reference_report
from deg_workspace import HIDDEN_ROOT, REPORT_JSON, run_pipeline, wipe_state


def test_deg_tb3_catalog_year_trap():
    """Hidden /opt/verifier-fixtures catalog-year-trap via TB3_FIXTURE_DIR override."""
    scenario = "catalog-year-trap"
    wipe_state()
    run_pipeline(scenario, fixture_root=HIDDEN_ROOT)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = reference_report(HIDDEN_ROOT, scenario)
    assert report["students"] == ref["students"]


def test_deg_tb3_subst_expiry_trap():
    """Hidden /opt/verifier-fixtures subst-expiry-trap rejects expired TB3 substitutions."""
    scenario = "subst-expiry-trap"
    wipe_state()
    run_pipeline(scenario, fixture_root=HIDDEN_ROOT)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = reference_report(HIDDEN_ROOT, scenario)
    assert report["students"] == ref["students"]
    assert any(r["satisfied"] for r in report["students"][0]["requirements"])
