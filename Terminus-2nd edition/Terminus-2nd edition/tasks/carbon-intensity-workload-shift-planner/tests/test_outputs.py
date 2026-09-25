"""Bundled shift-pl behavioral tests — ingest latch chain and export publish lane."""

from __future__ import annotations

import json
import subprocess

from shift_pl_cli_support import (
    APP,
    BIN,
    load_staging,
    pipeline,
    rebuild,
    scenario_root,
    wipe,
)
from shift_pl_oracle import carbon_mass, deadline_ok, reference_atlas


def test_tf332aa_baseload_matches_reference():
    """Baseload two-region atlas assignments must match the independent reference solver."""
    wipe()
    out = pipeline("baseload-two-region", "run-base")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(scenario_root() / "baseload-two-region", "run-base")
    assert rep["assignments"] == ref["assignments"]


def test_tf332aa_staging_ledger_fields():
    """Curated harmonized ledger must carry run_id, digest, and normalized window rows."""
    wipe()
    pipeline("baseload-two-region", "run-stg")
    stg = load_staging()
    assert stg["run_id"] == "run-stg"
    assert "harmonized_digest" in stg
    assert len(stg["normalized_windows"]) == 4


def test_tf332aa_carryover_quota_ledger():
    """Quota ledger carry_in/carry_out rows must match reference carryover policy."""
    wipe()
    out = pipeline("carryover-quota", "run-carry")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(scenario_root() / "carryover-quota", "run-carry")
    assert rep["quota_ledger"] == ref["quota_ledger"]


def test_tf332aa_residency_eu_only():
    """Residency-locked jobs must schedule only into the allowed EU region alias."""
    wipe()
    out = pipeline("residency-lock", "run-res")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(scenario_root() / "residency-lock", "run-res")
    assert rep["assignments"] == ref["assignments"]
    assert all(a["region"] == "R-EU" for a in rep["assignments"])


def test_tf332aa_deadline_inclusive_boundary():
    """Deadline-tight scenario must accept inclusive completion-slot feasibility."""
    wipe()
    out = pipeline("deadline-tight", "run-dead")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(scenario_root() / "deadline-tight", "run-dead")
    assert rep["assignments"] == ref["assignments"]


def test_tf332aa_intensity_sum_across_duration():
    """Carbon mass must sum intensity across every occupied slot of a multi-slot job."""
    wipe()
    out = pipeline("intensity-duration", "run-int")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(scenario_root() / "intensity-duration", "run-int")
    assert (
        rep["assignments"][0]["carbon_mass_g"] == ref["assignments"][0]["carbon_mass_g"]
    )


def test_tf332aa_infeasible_witness_sorted():
    """Blocked job rows must be ordered by job_id for deterministic atlas export."""
    wipe()
    out = pipeline("baseload-two-region", "run-infeas")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ids = [r["job_id"] for r in rep["blocked_jobs"]]
    assert ids == sorted(ids)


def test_tf332aa_plan_digest_stable():
    """plan_digest must be identical across repeated publishes of the same scenario."""
    wipe()
    out1 = pipeline("baseload-two-region", "run-dig")
    wipe()
    out2 = pipeline("baseload-two-region", "run-dig")
    d1 = json.loads(out1.read_text())["plan_digest"]
    d2 = json.loads(out2.read_text())["plan_digest"]
    assert d1 == d2


def test_tf332aa_export_reads_staging_only():
    """Publish must fail or emit empty assignments when the harmonized ledger is corrupted."""
    wipe()
    pipeline("baseload-two-region", "run-exp")
    APP.joinpath("state/shift-harmonized.json").write_text("{}", encoding="utf-8")
    out = APP / "output" / "broken.json"
    proc = subprocess.run(
        [str(BIN), "publish", "--run-id", "run-exp", "--output", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        proc.returncode != 0
        or not out.exists()
        or json.loads(out.read_text()).get("assignments") == []
    )


def test_tf332aa_reference_deadline_helper():
    """Independent deadline_ok helper encodes inclusive end-slot completion rules."""
    assert deadline_ok(1, 2, 2)
    assert not deadline_ok(2, 2, 2)


def test_tf332aa_reference_carbon_mass_helper():
    """Independent carbon_mass helper sums intensity across duration slots times compute."""
    assert carbon_mass([100.0, 50.0, 200.0], 2, 0, 2) == 300.0


def test_tf332aa_subprocess_double_rebuild():
    """Cargo rebuild must be idempotent when invoked twice before pytest."""
    rebuild()
    rebuild()


def test_tf332aa_assignments_sorted_by_job_id():
    """Published assignments must be sorted by job_id."""
    wipe()
    out = pipeline("baseload-two-region", "run-sort")
    ids = [a["job_id"] for a in json.loads(out.read_text())["assignments"]]
    assert ids == sorted(ids)


def test_tf332aa_summary_feasible_count():
    """Summary feasible_count must reflect at least one residency-feasible assignment."""
    wipe()
    out = pipeline("residency-lock", "run-sum")
    summary = json.loads(out.read_text())["summary"]
    assert summary["feasible_count"] >= 1


def test_tf332aa_quota_ledger_sorted():
    """Quota ledger rows must be sorted by region then window_index."""
    wipe()
    out = pipeline("carryover-quota", "run-ql")
    rows = json.loads(out.read_text())["quota_ledger"]
    keys = [(r["region"], r["window_index"]) for r in rows]
    assert keys == sorted(keys)


def test_tf332aa_stage_scenario_name_persisted():
    """Harmonized ledger must persist the latch scenario name across curate."""
    wipe()
    pipeline("intensity-duration", "run-name")
    assert load_staging()["scenario"] == "intensity-duration"


def test_tf332aa_total_carbon_mass_summary():
    """Summary total_carbon_mass_g must equal the sum of assignment carbon masses."""
    wipe()
    out = pipeline("intensity-duration", "run-tot")
    body = json.loads(out.read_text())
    total = body["summary"]["total_carbon_mass_g"]
    calc = sum(a["carbon_mass_g"] for a in body["assignments"])
    assert abs(total - calc) < 0.001


def test_tf332aa_ingest_stage_export_chain():
    """Full latch → curate → publish chain must emit a matching run_id atlas."""
    wipe()
    out = pipeline("baseload-two-region", "run-chain")
    assert out.exists()
    assert json.loads(out.read_text())["run_id"] == "run-chain"


def test_tf332aa_decoy_rank_not_in_atlas():
    """Decoy rank helper must not appear in published atlas JSON."""
    wipe()
    out = pipeline("baseload-two-region", "run-lexrank-control")
    text = out.read_text(encoding="utf-8")
    assert "rank_regions" not in text
    assert "decoy" not in text.lower()
