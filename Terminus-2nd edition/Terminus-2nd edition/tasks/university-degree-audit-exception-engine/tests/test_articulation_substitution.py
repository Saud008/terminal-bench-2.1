"""Transfer articulation, substitution expiry, and requirement rollup contract tests."""

from __future__ import annotations

import json

from registrar_graph_sim import reference_report
from deg_workspace import (
    FIXTURE_ROOT,
    REPORT_JSON,
    SCENARIO_CLOSURE,
    SCENARIO_SUBST,
    SCENARIO_TRANSFER,
    SCENARIO_WAIVER,
    run_pipeline,
    wipe_state,
)


def test_deg_transfer_equiv_maps_source_to_target():
    """Transfer-equiv scenario must map source transfer codes through articulation tables."""
    wipe_state()
    run_pipeline(SCENARIO_TRANSFER)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = reference_report(FIXTURE_ROOT, SCENARIO_TRANSFER)
    assert report["students"] == ref["students"]


def test_deg_substitution_active_applies_alt_requirement():
    """Substitution-active scenario must honor approved waiver substitutions."""
    wipe_state()
    run_pipeline(SCENARIO_SUBST)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = reference_report(FIXTURE_ROOT, SCENARIO_SUBST)
    assert report["students"] == ref["students"]


def test_deg_requirement_closure_rollup_matches_reference():
    """Requirement-closure scenario must propagate child credits to parent nodes."""
    wipe_state()
    run_pipeline(SCENARIO_CLOSURE)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = reference_report(FIXTURE_ROOT, SCENARIO_CLOSURE)
    assert report["students"] == ref["students"]
    core = max(
        report["students"][0]["requirements"],
        key=lambda row: row["required_credits"],
    )
    assert core["satisfied"] is True


def test_deg_exception_waiver_marks_eng_satisfied():
    """Exception-waiver scenario must satisfy waived requirements per registrar rules."""
    wipe_state()
    run_pipeline(SCENARIO_WAIVER)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = reference_report(FIXTURE_ROOT, SCENARIO_WAIVER)
    assert report["students"] == ref["students"]


def test_deg_waiver_core_requirement_eventually_satisfied():
    """Core requirement node must show satisfied after exception waiver merge."""
    wipe_state()
    run_pipeline(SCENARIO_WAIVER)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    core = max(
        report["students"][0]["requirements"],
        key=lambda row: row["required_credits"],
    )
    assert core["satisfied"] is True
