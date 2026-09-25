"""Bundled satellite imaging task plan manifest contract tests.

Pipeline stages under test: request ingest catalog, conflict-matrix audit buffer, manifest export emit.
"""

from __future__ import annotations

import sys

sys.path.insert(0, '/app/environment')

import json
import os
import random
from pathlib import Path

from verifier_contracts.satimg_contract_math import (
    MATRIX,
    assert_manifest_matches,
    load_scenario,
    read_matrix_meta,
    reference_from_scenario,
    reference_resolve,
    run_resolve,
    scenario_root,
    scrub_var,
)

OUT = "/app/output/"


def test_satimg7_pair_journal_row_count():
    """Staging snapshot conflict-matrix CSV row count matches assignment inventory."""
    run_resolve("dual-pass-basic", "plan-snap")
    meta = read_matrix_meta("plan-snap")
    assert meta["row_count"] == 3


def test_satimg7_dual_slot_basic_plan():
    """Dual-pass scenario manifest matches independent reference resolver."""
    out = run_resolve("dual-pass-basic", "dual-basic")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_scenario("dual-pass-basic", "dual-basic")
    assert_manifest_matches(body, ref)


def test_satimg7_pair_journal_csv_rows():
    """Resolve materializes conflict-matrix CSV rows under /app/var."""
    run_resolve("dual-pass-basic", "plan-stg")
    meta = read_matrix_meta("plan-stg")
    assert meta["row_count"] == 3
    lines = Path(MATRIX.format(token="plan-stg")).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 4


def test_satimg7_journal_meta_fingerprint():
    """Plan-buffer meta sidecar records matrix_fingerprint and run_token."""
    run_resolve("dual-pass-basic", "plan-meta")
    meta = read_matrix_meta("plan-meta")
    assert meta["run_token"] == "plan-meta"
    assert "matrix_fingerprint" in meta


def test_satimg7_temporal_clash_single():
    """Overlap trap allows only one stripmap assignment when setup padding applies."""
    out = run_resolve("overlap-trap", "overlap-one")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_scenario("overlap-trap", "overlap-one")
    assert body["assignment_count"] == 1
    assert_manifest_matches(body, ref)


def test_satimg7_rank_displace_winner():
    """Preemption trap displaces low rank request when high rank competes for same cell."""
    out = run_resolve("preempt-trap", "preempt-win")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_scenario("preempt-trap", "preempt-win")
    assert body["preemption_count"] == 1
    assert body["assignments"][0]["request_id"] == "R-high"
    assert_manifest_matches(body, ref)


def test_satimg7_risk_composite_pick():
    """Cloud blend trap picks pass with lower weighted composite score."""
    out = run_resolve("cloud-blend-trap", "cloud-pick")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_scenario("cloud-blend-trap", "cloud-pick")
    assert body["assignments"][0]["pass_id"] == "P2"
    assert_manifest_matches(body, ref)


def test_satimg7_dwell_warm_second():
    """Warm setup trap applies warm_setup_sec on consecutive same-mode pass assignments."""
    out = run_resolve("warm-setup-trap", "warm-setup")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_scenario("warm-setup-trap", "warm-setup")
    setups = sorted(a["setup_sec"] for a in body["assignments"])
    assert setups == [7, 14]
    assert_manifest_matches(body, ref)


def test_satimg7_journal_sort_order():
    """Staging CSV sorted by effective_start_sec then request_id."""
    run_resolve("staging-order-trap", "stg-order")
    lines = Path(MATRIX.format(token="stg-order")).read_text(encoding="utf-8").strip().splitlines()[1:]
    rows = []
    for line in lines:
        parts = line.split(",")
        rows.append({"effective_start_sec": int(parts[6]), "request_id": parts[0]})
    starts = [r["effective_start_sec"] for r in rows]
    assert starts == sorted(starts)
    ref = reference_from_scenario("staging-order-trap", "stg-order")
    body = json.loads(Path(f"{OUT}stg-order.json").read_text())
    assert_manifest_matches(body, ref)


def test_satimg7_plan_dest_under_output():
    """Caller --dest must land under /app/output/ per task-plan-manifest-schema.md."""
    dest = Path(f"{OUT}plan-dest.json")
    out = run_resolve("dual-pass-basic", "plan-dest", dest=dest)
    assert str(out).startswith("/app/output/")


def test_satimg7_plan_digest_stable():
    """plan_digest stable across repeated resolve with same token."""
    scrub_var()
    d1 = json.loads(run_resolve("dual-pass-basic", "plan-dig").read_text())["plan_digest"]
    scrub_var()
    d2 = json.loads(run_resolve("dual-pass-basic", "plan-dig").read_text())["plan_digest"]
    assert d1 == d2


def test_satimg7_scenario_bind_snapshot():
    """Scenario bind JSON snapshot written to /app/var/scenario-bind during resolve."""
    run_resolve("dual-pass-basic", "plan-bind")
    assert Path("/app/var/scenario-bind-plan-bind.json").is_file()


def test_satimg7_subprocess_rebuild_path():
    """Subprocess rebuild probe writes /app/output/subproc-check.json per verifier-contract-math.md."""
    out = run_resolve("dual-pass-basic", "plan-sub", dest=Path("/app/output/subproc-check.json"))
    assert Path("/app/output/subproc-check.json").is_file()
    assert str(out) == "/app/output/subproc-check.json"


def test_satimg7_constellation_id_echo():
    """Manifest constellation_id echoes scenario constellation identifier."""
    body = json.loads(run_resolve("dual-pass-basic", "plan-con").read_text())
    assert body["constellation_id"] == "LEO-A"


def test_satimg7_mean_risk_average():
    """mean_cloud_risk equals rounded mean of assignment cloud_composite values."""
    body = json.loads(run_resolve("dual-pass-basic", "plan-mean").read_text())
    ref = reference_from_scenario("dual-pass-basic", "plan-mean")
    assert body["mean_cloud_risk"] == ref["mean_cloud_risk"]


def test_satimg7_random_orbit_anti_hardcode():
    """Randomized orbit ids in synthetic scenario still match reference plan."""
    rng = random.Random(90210)
    meta = load_scenario("dual-pass-basic")
    for pw in meta["pass_windows"]:
        pw["orbit_id"] = f"O{rng.randint(10000, 99999)}"
    tmp = scenario_root() / "rnd-orbit-trap"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "scenario.json").write_text(json.dumps(meta), encoding="utf-8")
    os.environ["SAT_FIXTURE_ROOT"] = str(scenario_root())
    try:
        out = run_resolve("rnd-orbit-trap", "rnd-orbit")
        body = json.loads(out.read_text())
        ref = reference_resolve(meta)
        ref["run_token"] = "rnd-orbit"
        assert body["assignment_count"] == ref["assignment_count"]
        assert body["plan_digest"] == ref["plan_digest"]
    finally:
        os.environ.pop("SAT_FIXTURE_ROOT", None)


def test_satimg7_random_rank_anti_hardcode():
    """Randomized preempt ranks preserve deterministic winner under reference math."""
    rng = random.Random(44001)
    meta = load_scenario("preempt-trap")
    for c in meta["priority_contracts"]:
        c["preempt_rank"] = rng.randint(10, 99)
    meta["priority_contracts"][0]["preempt_rank"] = 20
    meta["priority_contracts"][1]["preempt_rank"] = 90
    tmp = scenario_root() / "rnd-priority-trap"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "scenario.json").write_text(json.dumps(meta), encoding="utf-8")
    os.environ["SAT_FIXTURE_ROOT"] = str(scenario_root())
    try:
        body = json.loads(run_resolve("rnd-priority-trap", "rnd-pri").read_text())
        ref = reference_resolve(meta)
        ref["run_token"] = "rnd-pri"
        assert_manifest_matches(body, ref)
    finally:
        os.environ.pop("SAT_FIXTURE_ROOT", None)


def test_satimg7_random_dwell_anti_hardcode():
    """Randomized setup durations still yield reference effective_start_sec values."""
    rng = random.Random(77123)
    meta = load_scenario("warm-setup-trap")
    for spec in meta["sensor_modes"].values():
        spec["cold_setup_sec"] = rng.randint(8, 20)
        spec["warm_setup_sec"] = rng.randint(4, 10)
    tmp = scenario_root() / "rnd-setup-trap"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "scenario.json").write_text(json.dumps(meta), encoding="utf-8")
    os.environ["SAT_FIXTURE_ROOT"] = str(scenario_root())
    try:
        body = json.loads(run_resolve("rnd-setup-trap", "rnd-setup").read_text())
        ref = reference_resolve(meta)
        ref["run_token"] = "rnd-setup"
        assert_manifest_matches(body, ref)
    finally:
        os.environ.pop("SAT_FIXTURE_ROOT", None)


def test_satimg7_effective_window_bounds():
    """Each assignment effective_end_sec equals effective_start_sec plus imaging_duration_sec."""
    body = json.loads(run_resolve("dual-pass-basic", "plan-bounds").read_text())
    meta = load_scenario("dual-pass-basic")
    durations = {r["request_id"]: r["imaging_duration_sec"] for r in meta["imaging_requests"]}
    for row in body["assignments"]:
        dur = durations[row["request_id"]]
        assert row["effective_end_sec"] == row["effective_start_sec"] + dur


def test_satimg7_displace_trace_shape():
    """preemption_trace entries name displaced and winner request ids."""
    body = json.loads(run_resolve("preempt-trap", "trace-shape").read_text())
    assert len(body["preemption_trace"]) == 1
    ev = body["preemption_trace"][0]
    assert ev["displaced_request_id"] == "R-low"
    assert ev["winner_request_id"] == "R-high"
