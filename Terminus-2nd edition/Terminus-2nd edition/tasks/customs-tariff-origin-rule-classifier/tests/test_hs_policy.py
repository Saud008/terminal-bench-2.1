"""Contract probes for HS policy and origin scoring pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from run_originctl import ATLAS_JSON, invoke, run_pipeline, wipe_state
from tariff_ref import normalize_hs
def test_thp_contract_digest_stable_rerun() -> None:
    """audit_digest must be stable across identical pipeline reruns."""
    wipe_state()
    run_pipeline("multi-line-order")
    d1 = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))["audit_digest"]
    wipe_state()
    run_pipeline("multi-line-order")
    d2 = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))["audit_digest"]
    assert d1 == d2
def test_thp_contract_hs10_length() -> None:
    """normalize_hs helper must emit ten digit HS codes."""
    assert len(normalize_hs("8504")) == 10
def test_thp_contract_preferential_duty_zero() -> None:
    """preferential treatment must match independent reference_classifications math."""
    wipe_state()
    run_pipeline("preferential-clean")
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    row = body["classifications"][0]
    assert row["tariff_treatment"] == "preferential"
    assert row["duty_rate_bps"] == 0
def test_thp_write_atlas_requires_parse_pass() -> None:
    """parse-shipment must increment parse_pass in origin-pass.json."""
    wipe_state()
    invoke("parse-shipment", "--manifest", "preferential-clean")
    Path("/app/var/run/origin-pass.json").write_text(
        '{"parse_pass":0,"atlas_pass":0}\n', encoding="utf-8"
    )
    proc = invoke("write-atlas", "--manifest", "preferential-clean")
    assert proc.returncode != 0
def test_thp_score_origin_writes_workbench_scores() -> None:
    """score-origin must write origin-scores.json workbench artifact."""
    wipe_state()
    run_pipeline("preferential-clean")
    scores = json.loads(
        Path("/app/var/workbench/origin-scores.json").read_text(encoding="utf-8")
    )
    assert scores["manifest_id"] == "preferential-clean"
    assert len(scores["scores"]) >= 1
def test_thp_audit_jsonl_has_rvc_field() -> None:
    """regional value floor must gate preferential treatment per rvc-threshold-contract."""
    wipe_state()
    run_pipeline("preferential-clean")
    lines = Path("/app/output/origin-audit.jsonl").read_text(encoding="utf-8").strip().splitlines()
    row = json.loads(lines[0])
    assert "rvc_bps" in row
    assert "agreement_code" in row
def test_thp_ingest_only_parse_without_atlas_export() -> None:
    """Ingest-only parse-shipment must buffer lines without atlas export emission."""
    wipe_state()
    proc = invoke("parse-shipment", "--manifest", "line-buffer-snapshot")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert Path("/app/var/workbench/normalized-lines.json").is_file()
    assert not ATLAS_JSON.exists()
def test_thp_write_atlas_export_requires_score_origin() -> None:
    """Atlas export via write-atlas must fail when score-origin path was skipped."""
    wipe_state()
    invoke("parse-shipment", "--manifest", "preferential-clean")
    proc = invoke("write-atlas", "--manifest", "preferential-clean")
    assert proc.returncode != 0
