"""PCDL TB3 hidden fixture traps."""

from __future__ import annotations

import json
import os

from demur_harness import FIXTURE_ROOT, HIDDEN_ROOT, INVOICE_JSON, drive_demur_pipeline, fetch_staged_dwell_rows, wipe_state
from demur_refmath import reference_invoices


def test_demur_T01_hidden_closure_hold():
    """Closure-calendar-contract: /opt/verifier-fixtures/demurctl hidden closure plus hold trap."""
    scenario = "hidden-closure-hold"
    wipe_state()
    drive_demur_pipeline(scenario, fixture_root=HIDDEN_ROOT)
    ref = reference_invoices(HIDDEN_ROOT, scenario)
    report = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]


def test_demur_T02_hidden_tier3_only():
    """Tariff-tier-contract: TB3_FIXTURE_DIR /opt/verifier-fixtures tier3-only scenario."""
    scenario = "hidden-tier3-only"
    wipe_state()
    drive_demur_pipeline(scenario, fixture_root=HIDDEN_ROOT)
    ref = reference_invoices(HIDDEN_ROOT, scenario)
    report = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]
    assert ref["lines"][0]["tier3_days"] >= 1


def test_demur_T03_demur_seed_override():
    """Engineering-problem-contract: DEMUR_SEED remaps container ids on yard load."""
    scenario = "basic-free-time"
    wipe_state()
    drive_demur_pipeline(
        scenario,
        extra_env={"DEMUR_SEED": "pcdl-trap-seed"},
    )
    ref = reference_invoices(FIXTURE_ROOT, scenario, seed="pcdl-trap-seed")
    report = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
    assert report["lines"] == ref["lines"]
    rows = fetch_staged_dwell_rows()
    assert rows[0]["container_id"].startswith("CNT-")


def test_demur_T04_tb3_fixture_dir_redirect():
    """CLI surface: TB3_FIXTURE_DIR /opt/verifier-fixtures redirects hidden yard loads."""
    scenario = "hidden-tier3-only"
    wipe_state()
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    try:
        drive_demur_pipeline(scenario, fixture_root=HIDDEN_ROOT, extra_env={"TB3_FIXTURE_DIR": str(HIDDEN_ROOT)})
        ref = reference_invoices(HIDDEN_ROOT, scenario)
        report = json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
        assert report["lines"] == ref["lines"]
    finally:
        os.environ.pop("TB3_FIXTURE_DIR", None)
