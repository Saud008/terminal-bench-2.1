"""Bundled customs tariff origin atlas scenarios."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from run_originctl import (
    ATLAS_JSON,
    DB_PATH,
    FIXTURE_ROOT,
    ORIGIN_BIN,
    WORKBENCH_LINES_JSON,
    invoke,
    run_pipeline,
    wipe_state,
)
from tariff_ref import normalize_hs, reference_classifications
def test_toa_smoke_parse_creates_sqlite_lines() -> None:
    """parse-shipment must create tariff.db line rows per shipment-parse-contract."""
    wipe_state()
    proc = invoke(
        "parse-shipment",
        "--manifest",
        "preferential-clean",
        "--fixture-dir",
        str(FIXTURE_ROOT),
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert DB_PATH.is_file()
    con = sqlite3.connect(DB_PATH)
    try:
        n = con.execute("SELECT COUNT(*) FROM lines").fetchone()[0]
    finally:
        con.close()
    assert n == 1
def test_toa_preferential_clean_matches_reference() -> None:
    """preferential treatment must match independent reference_classifications math."""
    wipe_state()
    run_pipeline("preferential-clean")
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_classifications("preferential-clean", FIXTURE_ROOT)
    assert body["classifications"] == ref["classifications"]
    assert body["audit_digest"] == ref["audit_digest"]
def test_toa_hs_pad_trailing_zeros() -> None:
    """HS normalization must pad to HS10 per hs-normalize-contract."""
    wipe_state()
    run_pipeline("hs-pad-trailing")
    ref = reference_classifications("hs-pad-trailing", FIXTURE_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_toa_rvc_below_floor_falls_to_mfn() -> None:
    """regional value floor must gate preferential treatment per rvc-threshold-contract."""
    wipe_state()
    run_pipeline("rvc-below-floor")
    ref = reference_classifications("rvc-below-floor", FIXTURE_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_toa_cert_expiry_inclusive_last_day() -> None:
    """certificate expiry last day must remain valid per certificate-window-contract."""
    wipe_state()
    run_pipeline("cert-expiry-edge")
    ref = reference_classifications("cert-expiry-edge", FIXTURE_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_toa_precedence_longest_prefix_wins() -> None:
    """agreement precedence must pick lowest priority per origin-precedence-contract."""
    wipe_state()
    run_pipeline("precedence-specific")
    ref = reference_classifications("precedence-specific", FIXTURE_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"][0]["agreement_code"] == ref["classifications"][0]["agreement_code"]
def test_toa_multi_line_sorted_output() -> None:
    """classifications must sort by line_id per atlas-emit-contract."""
    wipe_state()
    run_pipeline("multi-line-order")
    ref = reference_classifications("multi-line-order", FIXTURE_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_toa_missing_certificate_mfn() -> None:
    """missing certificate must yield MFN treatment."""
    wipe_state()
    run_pipeline("missing-certificate")
    ref = reference_classifications("missing-certificate", FIXTURE_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_toa_cert_before_issue_invalid() -> None:
    """shipment before certificate issue must invalidate preferential path."""
    wipe_state()
    run_pipeline("cert-before-issue")
    ref = reference_classifications("cert-before-issue", FIXTURE_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_toa_tie_break_agreement_lexicographic() -> None:
    """equal priority agreements must break lexicographically."""
    wipe_state()
    run_pipeline("tie-agreement-code")
    ref = reference_classifications("tie-agreement-code", FIXTURE_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_toa_parse_pass_increments() -> None:
    """parse-shipment must increment parse_pass in origin-pass.json."""
    wipe_state()
    run_pipeline("preferential-clean")
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["parse_pass"] == 1
def test_toa_line_buffer_snapshot_hs_normalized() -> None:
    """normalized-lines.json workbench buffer must store HS10 codes."""
    wipe_state()
    run_pipeline("line-buffer-snapshot")
    snap = json.loads(WORKBENCH_LINES_JSON.read_text(encoding="utf-8"))
    assert snap["lines"][0]["hs_normalized"] == normalize_hs("9018.19.95")
def test_toa_importer_id_persisted_meta() -> None:
    """importer_id must persist in ledger meta table."""
    wipe_state()
    run_pipeline("preferential-clean")
    con = sqlite3.connect(DB_PATH)
    try:
        imp = con.execute("SELECT value FROM meta WHERE key='importer_id'").fetchone()[0]
    finally:
        con.close()
    assert imp == "IMP-K7Q2M9"
def test_toa_decoy_not_linked() -> None:
    """decoy parityhint module must not import atlas emitters."""
    src = Path("/app/internal/decoy/parityhint/preview.go").read_text(encoding="utf-8")
    assert "github.com/terminus/originctl/internal/classout" not in src


def test_toa_output_path_absolute() -> None:
    """CLI output paths must match instruction absolute paths."""
    assert ATLAS_JSON.as_posix() == "/app/output/tariff-classifications.json"
    assert ORIGIN_BIN == "/app/bin/originctl"
