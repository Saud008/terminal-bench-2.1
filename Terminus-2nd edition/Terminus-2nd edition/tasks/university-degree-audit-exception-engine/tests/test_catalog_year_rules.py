"""Catalog year and locked curriculum filtering contract tests for degaudit."""

from __future__ import annotations

import json

from registrar_graph_sim import reference_report
from deg_workspace import (
    FIXTURE_ROOT,
    REPORT_JSON,
    SCENARIO_CATALOG,
    SCENARIO_REPEAT,
    run_pipeline,
    wipe_state,
)


def test_deg_catalog_year_lock_excludes_legacy_course():
    """Catalog-year-lock scenario must exclude legacy courses per locked year rules."""
    wipe_state()
    run_pipeline(SCENARIO_CATALOG)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = reference_report(FIXTURE_ROOT, SCENARIO_CATALOG)
    assert report["students"] == ref["students"]


def test_deg_repeat_retake_keeps_highest_grade():
    """Repeat-retake scenario must fold enrollments to the highest grade per course."""
    wipe_state()
    run_pipeline(SCENARIO_REPEAT)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    ref = reference_report(FIXTURE_ROOT, SCENARIO_REPEAT)
    assert report["students"] == ref["students"]
    math_rows = [r for r in report["students"][0]["requirements"] if "math" in r["req_id"] or r["satisfied"]]
    assert any(r["satisfied"] for r in math_rows)


def test_deg_catalog_scenario_core_partial_without_legacy():
    """Core requirement credits must not exceed required credits when legacy courses are excluded."""
    wipe_state()
    run_pipeline(SCENARIO_CATALOG)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    core = max(
        report["students"][0]["requirements"],
        key=lambda row: row["required_credits"],
    )
    assert core["satisfied_credits"] <= core["required_credits"]
