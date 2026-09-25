"""Contract alignment tests for seismocomply exceedance math."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from seismocomply_cli_support import APP_ROOT, BUFFER_PATH, CATALOG, SEED_POOL, SURVEY_DIR, run_pipeline, wipe
from seismocomply_contract_math import load_survey, reference_atlas


@pytest.fixture(autouse=True)
def _clean():
    wipe()
    yield
    wipe()


def _survey_path(name: str) -> Path:
    return SURVEY_DIR / f"{name}.json"


def test_buffer_correlate_seq_increments_cross_survey():
    """Peak correlation buffer correlate_seq must increment when the same seed loads a new survey."""
    seed = SEED_POOL[0]
    s1, s2 = CATALOG["surveys"][0], CATALOG["surveys"][1]
    run_pipeline(seed, s1)
    buf1 = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    run_pipeline(seed, s2)
    buf2 = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    assert buf2["correlate_seq"] == buf1["correlate_seq"] + 1


def test_exceedance_rows_match_reference_survey0():
    """Exceedance rows must match independent reference math for bundled survey zero."""
    seed = "ref-seed-a"
    survey = CATALOG["surveys"][0]
    out = run_pipeline(seed, survey)
    got = json.loads(out.read_text(encoding="utf-8"))
    record = load_survey(_survey_path(survey))
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    exp = reference_atlas(seed, survey, record, buf["correlate_seq"])
    assert got["exceedance_rows"] == exp["exceedance_rows"]


def test_atlas_digest_matches_reference():
    """atlas_digest must match canonical summary hash from independent reference."""
    seed = SEED_POOL[3]
    survey = CATALOG["surveys"][2]
    out = run_pipeline(seed, survey)
    got = json.loads(out.read_text(encoding="utf-8"))
    record = load_survey(_survey_path(survey))
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    exp = reference_atlas(seed, survey, record, buf["correlate_seq"])
    assert got["atlas_digest"] == exp["atlas_digest"]


def test_row_sort_order_property_blast_sensor():
    """Exceedance rows must sort by property_id, blast_id, then sensor_id per atlas-publish-fields."""
    seed = SEED_POOL[1]
    survey = CATALOG["surveys"][3]
    out = run_pipeline(seed, survey)
    rows = json.loads(out.read_text(encoding="utf-8"))["exceedance_rows"]
    keys = [(r["property_id"], r["blast_id"], r["sensor_id"]) for r in rows]
    assert keys == sorted(keys)


def test_audit_run_id_format():
    """audit_run_id must be audit- prefix plus SHA-256 scoped to seed, survey, and correlate_seq."""
    seed = SEED_POOL[2]
    survey = CATALOG["surveys"][1]
    out = run_pipeline(seed, survey)
    got = json.loads(out.read_text(encoding="utf-8"))
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    record = load_survey(_survey_path(survey))
    exp = reference_atlas(seed, survey, record, buf["correlate_seq"])
    assert got["audit_run_id"] == exp["audit_run_id"]
    assert got["audit_run_id"].startswith("audit-")


def test_summary_exceedance_count_matches_rows():
    """summary.exceedance_count must equal the number of rows with exceeded true."""
    seed = SEED_POOL[0]
    survey = CATALOG["surveys"][2]
    out = run_pipeline(seed, survey)
    rep = json.loads(out.read_text(encoding="utf-8"))
    counted = sum(1 for r in rep["exceedance_rows"] if r["exceeded"])
    assert rep["summary"]["exceedance_count"] == counted


def test_attenuation_uses_boundary_not_sensor_distance():
    """distance_m must use closest boundary vertex anchor, not sensor mount coordinates."""
    seed = "anchor-check"
    survey = CATALOG["surveys"][0]
    out = run_pipeline(seed, survey)
    rows = json.loads(out.read_text(encoding="utf-8"))["exceedance_rows"]
    record = load_survey(_survey_path(survey))
    exp = reference_atlas(seed, survey, record, 1)
    assert rows[0]["distance_m"] == exp["exceedance_rows"][0]["distance_m"]


def test_night_threshold_applies_for_late_blast():
    """Night regulatory limits must apply when blast fired_at falls outside local day hours."""
    seed = "night-thresh"
    survey = CATALOG["surveys"][3]
    out = run_pipeline(seed, survey)
    got = json.loads(out.read_text(encoding="utf-8"))
    record = load_survey(_survey_path(survey))
    fired = record["blasts"][0]["fired_at"]
    if int(fired[11:13]) >= 19 or int(fired[11:13]) < 7:
        row = got["exceedance_rows"][0]
        assert row["threshold_mm_s"] == record["limits"]["residential"]["night_mm_s"] or row["threshold_mm_s"] == record["limits"]["industrial"]["night_mm_s"]


def test_calibration_gain_order_raw_minus_offset():
    """Sensor calibration must apply zero offset before gain multiplier per calibration contract."""
    seed = "gain-order"
    survey = CATALOG["surveys"][1]
    out = run_pipeline(seed, survey)
    got = json.loads(out.read_text(encoding="utf-8"))
    record = load_survey(_survey_path(survey))
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    exp = reference_atlas(seed, survey, record, buf["correlate_seq"])
    assert got["exceedance_rows"] == exp["exceedance_rows"]


def test_scaled_distance_reference_in_denominator():
    """Attenuation must place reference_distance_m in the numerator per distance-attenuation contract."""
    seed = "atten-ref"
    survey = CATALOG["surveys"][2]
    out = run_pipeline(seed, survey)
    got = json.loads(out.read_text(encoding="utf-8"))
    record = load_survey(_survey_path(survey))
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    exp = reference_atlas(seed, survey, record, buf["correlate_seq"])
    assert got["exceedance_rows"] == exp["exceedance_rows"]


def test_combined_ppv_is_max_of_corrected_and_attenuated():
    """Row attenuated_ppv_mm_s must be max of corrected reading and attenuated prediction."""
    seed = "max-blend"
    survey = CATALOG["surveys"][0]
    out = run_pipeline(seed, survey)
    got = json.loads(out.read_text(encoding="utf-8"))
    record = load_survey(_survey_path(survey))
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    exp = reference_atlas(seed, survey, record, buf["correlate_seq"])
    for g, e in zip(got["exceedance_rows"], exp["exceedance_rows"], strict=True):
        assert g["attenuated_ppv_mm_s"] == e["attenuated_ppv_mm_s"]


def test_cross_run_persistence_reset():
    """After clear-seismo-run.sh correlate_seq must restart at one for the same seed and survey."""
    seed = SEED_POOL[3]
    survey = CATALOG["surveys"][0]
    run_pipeline(seed, survey)
    wipe()
    run_pipeline(seed, survey)
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    assert buf["correlate_seq"] == 1


def test_randomized_overlay_survey_anti_hardcode():
    """Runtime overlay surveys with randomized ids and coordinates must match reference math."""
    rng = random.Random(90210)
    seed = f"rand-{rng.randint(1000, 9999)}"
    survey = f"dyn-{rng.randint(10000, 99999)}"
    bx, by = rng.uniform(100, 200), rng.uniform(5000, 5100)
    pid = f"P-{rng.randint(10000, 99999)}"
    sid = f"S-{rng.randint(10000, 99999)}"
    bid = f"B-{rng.randint(10000, 99999)}"
    overlay = {
        "survey": survey,
        "reference_distance_m": 50.0,
        "attenuation_exponent": 1.5,
        "timezone_offset_hours": 10,
        "blasts": [
            {
                "blast_id": bid,
                "easting_m": round(bx, 3),
                "northing_m": round(by, 3),
                "source_ppv_mm_s": round(rng.uniform(6.0, 12.0), 4),
                "fired_at": "2026-05-10T08:00:00Z",
            }
        ],
        "properties": [
            {
                "property_id": pid,
                "structure_class": "residential",
                "boundary_vertices": [
                    [round(bx + 120, 3), round(by + 80, 3)],
                    [round(bx + 150, 3), round(by + 80, 3)],
                    [round(bx + 150, 3), round(by + 110, 3)],
                    [round(bx + 120, 3), round(by + 110, 3)],
                ],
            }
        ],
        "sensors": [
            {
                "sensor_id": sid,
                "property_id": pid,
                "easting_m": round(bx + 135, 3),
                "northing_m": round(by + 95, 3),
                "gain_multiplier": round(rng.uniform(0.95, 1.05), 4),
                "zero_offset_mm_s": round(rng.uniform(-0.1, 0.1), 4),
            }
        ],
        "readings": [
            {
                "blast_id": bid,
                "sensor_id": sid,
                "raw_ppv_mm_s": round(rng.uniform(2.0, 6.0), 4),
                "peak_timestamp": "2026-05-10T08:00:00Z",
            }
        ],
        "limits": {
            "residential": {"day_mm_s": round(rng.uniform(4.0, 6.0), 2), "night_mm_s": round(rng.uniform(1.5, 2.5), 2)},
            "industrial": {"day_mm_s": 10.0, "night_mm_s": 5.0},
        },
    }
    overlay_dir = APP_ROOT / "output" / "overlay-surveys"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    (overlay_dir / f"{survey}.json").write_text(json.dumps(overlay) + "\n", encoding="utf-8")
    out = run_pipeline(seed, survey, fixture_dir=overlay_dir)
    got = json.loads(out.read_text(encoding="utf-8"))
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    exp = reference_atlas(seed, survey, overlay, buf["correlate_seq"])
    assert got["exceedance_rows"] == exp["exceedance_rows"]
    assert got["atlas_digest"] == exp["atlas_digest"]


def test_bundled_survey_catalog_count():
    """Bundled survey catalog must include at least four surveys for verifier depth."""
    assert len(CATALOG["surveys"]) >= 4


def test_active_passport_replaced_on_seed_restage():
    """A new correlate pass for the same seed must replace the active audit passport row."""
    seed = SEED_POOL[0]
    s1, s2 = CATALOG["surveys"][0], CATALOG["surveys"][2]
    run_pipeline(seed, s1)
    pass1 = json.loads((APP_ROOT / "work" / "audit-passport.json").read_text(encoding="utf-8"))
    run_pipeline(seed, s2)
    pass2 = json.loads((APP_ROOT / "work" / "audit-passport.json").read_text(encoding="utf-8"))
    assert pass2["active"]["survey"] == s2
    assert pass1["active"]["audit_run_id"] != pass2["active"]["audit_run_id"]
