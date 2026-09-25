"""Bundled gclint behavioral tests."""

from __future__ import annotations

import json
from pathlib import Path

from gclint_cli_support import APP, STAGING, run_pipeline, wipe
from gclint_contract_math import expand_jobs, load_pipeline, reference_contract_report, rules_fingerprint, staging_digest


def test_ingest_analyze_export_matrix_basic():
    """Bundled matrix-basic ingest analyze export matches independent contract math."""
    wipe()
    out = run_pipeline("matrix-basic", "run-alpha")
    rep = json.loads(out.read_text(encoding="utf-8"))
    contract = reference_contract_report(Path("/app/fixtures/pipelines/matrix-basic.yml"), "run-alpha")
    assert rep["summary"]["error"] == contract["summary"]["error"]
    assert len(rep["findings"]) == len(contract["findings"])


def test_staging_snapshot_schema():
    """Staging file includes run_id, digest, rules_fingerprint, and jobs list."""
    wipe()
    run_pipeline("matrix-basic", "run-bravo")
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap["run_id"] == "run-bravo"
    assert "staging_digest" in snap
    assert "rules_fingerprint" in snap
    assert isinstance(snap["jobs"], list)


def test_matrix_duplicate_detection():
    """matrix-duplicate pipeline marks at least one duplicate matrix expansion row."""
    wipe()
    run_pipeline("matrix-duplicate", "run-charlie")
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    dups = [j for j in snap["jobs"] if j.get("duplicate")]
    assert len(dups) >= 1


def test_rules_first_match_never():
    """rules-never pipeline keeps lint job inactive with when never."""
    wipe()
    run_pipeline("rules-never", "run-delta")
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    lint = [j for j in snap["jobs"] if j["name"] == "lint"][0]
    assert lint["when"] == "never"
    assert lint["active"] is False


def test_optional_needs_missing_job_ok():
    """optional-needs must not emit NEED_MISSING for optional missing producers."""
    wipe()
    out = run_pipeline("optional-needs", "run-alpha")
    rep = json.loads(out.read_text(encoding="utf-8"))
    codes = {f["code"] for f in rep["findings"]}
    assert "NEED_MISSING" not in codes or all("missing:job" not in f["message"] for f in rep["findings"])


def test_stage_order_violation_reported():
    """stage-violation export includes STAGE_ORDER finding code."""
    wipe()
    out = run_pipeline("stage-violation", "run-bravo")
    rep = json.loads(out.read_text(encoding="utf-8"))
    codes = {f["code"] for f in rep["findings"]}
    assert "STAGE_ORDER" in codes


def test_export_audit_digest_stable():
    """Repeated matrix-basic runs yield identical non-broken audit_digest values."""
    wipe()
    out1 = run_pipeline("matrix-basic", "run-alpha")
    wipe()
    out2 = run_pipeline("matrix-basic", "run-alpha")
    d1 = json.loads(out1.read_text(encoding="utf-8"))["audit_digest"]
    d2 = json.loads(out2.read_text(encoding="utf-8"))["audit_digest"]
    assert d1 == d2
    assert d1 != "broken"


def test_staging_digest_includes_rules_fingerprint():
    """Staging digest incorporates rules_fingerprint per staging-snapshot-schema.md."""
    wipe()
    run_pipeline("rules-never", "run-charlie")
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    pipeline = load_pipeline(Path("/app/fixtures/pipelines/rules-never.yml"))
    jobs = expand_jobs(pipeline)
    fp = rules_fingerprint(jobs)
    expected = staging_digest("run-charlie", jobs, fp)
    assert snap.get("rules_fingerprint") == fp
    assert snap.get("staging_digest") == expected


def test_matrix_canonical_name_sorting():
    """Matrix suffix keys sort lexicographically regardless of declaration order."""
    from gclint_contract_math import matrix_name

    a = matrix_name("test", {"OS": "linux", "ARCH": "amd64"})
    b = matrix_name("test", {"ARCH": "amd64", "OS": "linux"})
    assert a == b


def test_artifact_chain_no_closure_error():
    """artifact-chain pipeline must not report ARTIFACT_CLOSURE when paths align."""
    wipe()
    out = run_pipeline("artifact-chain", "run-delta")
    rep = json.loads(out.read_text(encoding="utf-8"))
    codes = {f["code"] for f in rep["findings"]}
    assert "ARTIFACT_CLOSURE" not in codes


def test_export_reads_staging_not_ingest_only():
    """Export still succeeds after corrupting ingest work file when staging remains valid."""
    wipe()
    run_pipeline("matrix-basic", "run-alpha")
    staging_mtime = STAGING.stat().st_mtime
    ingest = APP / "work" / "run-alpha-ingest.json"
    ingest.write_text("{}", encoding="utf-8")
    out = APP / "output" / "run-alpha-reexport.json"
    from gclint_cli_support import CLI, invoke

    proc = invoke([str(CLI), "export", "--run-id", "run-alpha", "--output", str(out)])
    assert proc.returncode == 0
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["findings"] != [] or rep["audit_digest"] != "broken"
    assert STAGING.stat().st_mtime >= staging_mtime


def test_findings_sorted_by_job_then_code():
    """Export findings array is sorted by job name then finding code."""
    wipe()
    out = run_pipeline("stage-violation", "run-charlie")
    rep = json.loads(out.read_text(encoding="utf-8"))
    keys = [(f["job"], f["code"]) for f in rep["findings"]]
    assert keys == sorted(keys)


def test_subprocess_cli_ingest_idempotent():
    """Repeated ingest plus analyze leaves staging snapshot on disk."""
    wipe()
    from gclint_cli_support import CLI, invoke

    for _ in range(2):
        proc = invoke([str(CLI), "ingest", "--pipeline", "matrix-basic", "--run-id", "run-bravo"])
        assert proc.returncode == 0
    proc = invoke([str(CLI), "analyze", "--run-id", "run-bravo"])
    assert proc.returncode == 0
    assert STAGING.exists()


def test_active_job_count_matrix_basic():
    """matrix-basic staging lists three active jobs after rules evaluation."""
    wipe()
    run_pipeline("matrix-basic", "run-alpha")
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    active = [j for j in snap["jobs"] if j["active"]]
    assert len(active) == 3


def test_needs_array_preserved_in_staging():
    """optional-needs staging retains parsed needs edges on expanded jobs."""
    wipe()
    run_pipeline("optional-needs", "run-bravo")
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    test_job = [j for j in snap["jobs"] if "test" in j["name"]][0]
    assert len(test_job["needs"]) >= 2


def test_summary_error_count_matches_findings():
    """Export summary error counter equals error-severity findings count."""
    wipe()
    out = run_pipeline("stage-violation", "run-delta")
    rep = json.loads(out.read_text(encoding="utf-8"))
    err = sum(1 for f in rep["findings"] if f["severity"] == "error")
    assert rep["summary"]["error"] == err


def test_pipeline_catalog_file_exists():
    """pipeline-catalog.md documents bundled verifier scenarios."""
    assert (APP / "docs" / "pipeline-catalog.md").is_file()


def test_reset_state_clears_staging():
    """reset-state.sh removes staging snapshot between cross-run cases."""
    wipe()
    run_pipeline("matrix-basic", "run-alpha")
    wipe()
    assert not STAGING.exists() or STAGING.read_text(encoding="utf-8") == ""
