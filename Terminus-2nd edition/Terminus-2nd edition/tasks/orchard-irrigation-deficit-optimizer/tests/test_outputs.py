"""Bundled behavioral tests using reference_plan math from irrctl_plan_math."""

from __future__ import annotations

import json
from pathlib import Path

from irrctl_subprocess_helpers import pipeline, rebuild, orchard_root, wipe, load_ledger
from irrctl_plan_math import (
    independent_plan,
    calibrated_vwc,
    weighted_blend,
    deficit_mm,
    assert_assignments_close,
    assert_trace_close,
    assert_quota_close,
)

MOISTURE_LEDGER_PATH = "/app/state/moisture-ledger.json"
OUTPUT_DIR_PREFIX = "/app/output/"


def test_tca9cd4_oido_twin_field_matches_independent():
    """Twin-field scenario plan assignments match independent plan math."""
    wipe()
    out = pipeline("twin-field-basic", "run-twin")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = independent_plan(orchard_root() / "twin-field-basic", "run-twin")
    assert_assignments_close(rep["assignments"], ref["assignments"])


def test_tca9cd4_oido_orchardst_ledger_fields():
    """build-ledger writes moisture ledger with run_id, digest, and per-field rows."""
    wipe()
    run_id = "run-stg"
    pipeline("twin-field-basic", run_id)
    stg = load_ledger()
    assert stg["run_id"] == run_id
    assert "ledger_digest" in stg
    assert len(stg["fields"]) == 2


def test_tca9cd4_oido_orchardmo_ledger_path():
    """Moisture ledger snapshot at /app/state/moisture-ledger.json after load-pack ingest and build-ledger staging."""
    wipe()
    run_id = "run-ledger-path"
    pipeline("twin-field-basic", run_id)
    ledger_path = Path(MOISTURE_LEDGER_PATH)
    assert ledger_path.is_file()
    assert json.loads(ledger_path.read_text(encoding="utf-8"))["run_id"] == run_id


def test_tca9cd4_oido_plan_output_under_app_output():
    """publish-plan export writes caller output under /app/output/ after moisture ledger staging."""
    wipe()
    run_id = "run-out-path"
    out_path = Path(f"{OUTPUT_DIR_PREFIX}{run_id}.json")
    out = pipeline("twin-field-basic", run_id, out=out_path)
    assert str(out).startswith(OUTPUT_DIR_PREFIX)
    assert out.is_file()


def test_tca9cd4_oido_probe_offset_calibration():
    """Probe calibration offsets from probe-calibration-contract affect assignments."""
    wipe()
    out = pipeline("probe-offset-trap", "run-off")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = independent_plan(orchard_root() / "probe-offset-trap", "run-off")
    assert_assignments_close(rep["assignments"], ref["assignments"])


def test_tca9cd4_oido_crop_stage_kc_index():
    """Crop-stage Kc lookup drives deficit trace rows per crop-stage-kc-curve."""
    wipe()
    out = pipeline("crop-stage-kc", "run-kc")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = independent_plan(orchard_root() / "crop-stage-kc", "run-kc")
    assert_trace_close(rep["deficit_trace"], ref["deficit_trace"])


def test_tca9cd4_oido_quota_carryover_ledger():
    """District quota windows with carryover populate quota_ledger per quota-window-carryover."""
    wipe()
    out = pipeline("quota-carryover", "run-quota")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = independent_plan(orchard_root() / "quota-carryover", "run-quota")
    assert_quota_close(rep["quota_ledger"], ref["quota_ledger"])


def test_tca9cd4_oido_pump_capacity_limits_total_liters():
    """Pump capacity contract caps total applied liters across assignments."""
    wipe()
    out = pipeline("pump-limited", "run-pump")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = independent_plan(orchard_root() / "pump-limited", "run-pump")
    assert_assignments_close(rep["assignments"], ref["assignments"])
    total = sum(a["liters_applied"] for a in rep["assignments"])
    assert total <= 100.0 + 1e-6


def test_tca9cd4_oido_weighted_probe_blend():
    """Area-weighted probe blending changes assignments per probe-blend-contract."""
    wipe()
    out = pipeline("blend-weights", "run-blend")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = independent_plan(orchard_root() / "blend-weights", "run-blend")
    assert_assignments_close(rep["assignments"], ref["assignments"])


def test_tca9cd4_oido_assignments_sorted():
    """Plan assignments are sorted by field_id then window_index per irrigation-plan-schema."""
    wipe()
    out = pipeline("twin-field-basic", "run-sort")
    keys = [(a["field_id"], a["window_index"]) for a in json.loads(out.read_text())["assignments"]]
    assert keys == sorted(keys)


def test_tca9cd4_oido_deficit_trace_sorted():
    """Deficit trace rows are sorted by field_id then window_index."""
    wipe()
    out = pipeline("twin-field-basic", "run-wit")
    keys = [(r["field_id"], r["window_index"]) for r in json.loads(out.read_text())["deficit_trace"]]
    assert keys == sorted(keys)


def test_tca9cd4_oido_plan_orcharddi_stable():
    """plan_digest is stable across repeated publish-plan for the same orchard pack."""
    wipe()
    d1 = json.loads(pipeline("twin-field-basic", "run-dig").read_text())["plan_digest"]
    wipe()
    d2 = json.loads(pipeline("twin-field-basic", "run-dig").read_text())["plan_digest"]
    assert d1 == d2


def test_tca9cd4_oido_summary_total_liters():
    """Summary total_liters equals sum of assignment liters_applied."""
    wipe()
    body = json.loads(pipeline("twin-field-basic", "run-sum").read_text())
    calc = sum(a["liters_applied"] for a in body["assignments"])
    assert abs(body["summary"]["total_liters"] - calc) < 0.001


def test_tca9cd4_oido_math_calibrated_vwc():
    """Calibrated VWC subtracts probe offset per probe-calibration-contract."""
    assert abs(calibrated_vwc(0.24, 0.02) - 0.22) < 1e-9


def test_tca9cd4_oido_math_deficit_includes_et():
    """Deficit scoring adds ET demand millimeters per deficit-scoring-contract."""
    assert deficit_mm(2.0, 3.0) == 5.0


def test_tca9cd4_oido_math_weighted_blend():
    """Weighted blend matches probe-blend-contract area weights."""
    probes = [
        {"raw_vwc": 0.20, "offset": 0.0, "weight": 0.9},
        {"raw_vwc": 0.40, "offset": 0.0, "weight": 0.1},
    ]
    assert abs(weighted_blend(probes) - 0.22) < 1e-9


def test_tca9cd4_oido_subprocess_double_rebuild():
    """Repeated cargo rebuild before CLI invocation remains deterministic."""
    rebuild()
    rebuild()


def test_tca9cd4_oido_orchardin_stage_orchardex_chain():
    """load-pack, build-ledger, and publish-plan chain produces plan JSON at output path."""
    wipe()
    run_id = "run-chain"
    out = pipeline("twin-field-basic", run_id)
    assert out.exists()
    assert json.loads(out.read_text())["run_id"] == run_id


def test_tca9cd4_oido_orchardst_orcheard_name():
    """Moisture ledger records orchard name from loaded field pack."""
    wipe()
    pipeline("crop-stage-kc", "run-name")
    assert load_ledger()["orchard"] == "crop-stage-kc"


def test_tca9cd4_oido_quota_ledger_window_order():
    """quota_ledger rows are sorted by window_index."""
    wipe()
    rows = json.loads(pipeline("quota-carryover", "run-ql").read_text())["quota_ledger"]
    assert [r["window_index"] for r in rows] == sorted(r["window_index"] for r in rows)


def test_tca9cd4_oido_assignment_count_summary():
    """Summary assignment_count reflects non-empty assignment list."""
    wipe()
    summary = json.loads(pipeline("pump-limited", "run-ac").read_text())["summary"]
    assert summary["assignment_count"] >= 1
