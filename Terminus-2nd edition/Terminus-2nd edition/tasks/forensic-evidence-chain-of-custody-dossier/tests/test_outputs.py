"""Primary verifier tests for rvk9."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from custody_cli_helpers import run_pipeline, wipe
from custody_verifier_math import reference_dossier

APP = Path("/app")
FIX = APP / "fixtures" / "cases"
CAT = APP / "catalog" / "storage-locations.json"


def test_rvk9_binary_installed_for_subprocess_cli() -> None:
    """Verify rvk9 binary exists for subprocess CLI invocation."""
    subprocess.run(["test", "-x", str(APP / "bin" / "rvk9")], check=True)


def test_metro_gun_chain_dossier_matches_reference() -> None:
    """Verify metro-gun-chain dossier matches independent custody math."""
    wipe()
    case_id = "CASE-METRO-441"
    out = run_pipeline(case_id, "metro-gun-chain")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_dossier(case_id, FIX / "metro-gun-chain.json", CAT)
    assert got["summary"] == ref["summary"]
    assert got["lineage_edges"] == ref["lineage_edges"]
    assert got["integrity_findings"] == ref["integrity_findings"]
    assert got["custody_digest"] == ref["custody_digest"]


def test_custody_vault_written_on_load() -> None:
    """Verify vault load ingest stage writes custody-vault snapshot at /app/var/custody-vault.json."""
    wipe()
    run_pipeline("CASE-METRO-441", "metro-gun-chain")
    snap = json.loads((APP / "var" / "custody-vault.json").read_text(encoding="utf-8"))
    assert snap["case_id"] == "CASE-METRO-441"
    assert snap["bundle_id"] == "metro-gun-chain"
    assert snap["run_seq"] >= 1


def test_register_seq_matches_vault_run_seq() -> None:
    """Verify exhibit register ledger ledger_seq equals transfer vault run_seq."""
    wipe()
    run_pipeline("CASE-METRO-441", "metro-gun-chain")
    snap = json.loads((APP / "var" / "custody-vault.json").read_text(encoding="utf-8"))
    ledger = json.loads((APP / "var" / "exhibit-register.json").read_text(encoding="utf-8"))
    assert ledger["ledger_seq"] == snap["run_seq"]


def test_run_seq_increments_on_rerun() -> None:
    """Verify run_seq monotonicity across repeated vault load for same case."""
    wipe()
    run_pipeline("CASE-METRO-441", "metro-gun-chain")
    snap1 = json.loads((APP / "var" / "custody-vault.json").read_text(encoding="utf-8"))
    run_pipeline("CASE-METRO-441", "metro-gun-chain")
    snap2 = json.loads((APP / "var" / "custody-vault.json").read_text(encoding="utf-8"))
    assert snap2["run_seq"] > snap1["run_seq"]


def test_seal_break_trap_detected() -> None:
    """Verify seal mismatch on transfer row emits seal_break finding."""
    wipe()
    out = run_pipeline("CASE-METRO-442", "seal-break-trap")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_dossier("CASE-METRO-442", FIX / "seal-break-trap.json", CAT)
    assert got["summary"]["seal_breaks"] == ref["summary"]["seal_breaks"] == 1
    assert any(b["code"] == "seal_break" for b in got["integrity_findings"])


def test_lab_submit_before_transfer_is_chronology_violation() -> None:
    """Verify lab_submit before latest transfer emits chronology_violation."""
    wipe()
    out = run_pipeline("CASE-METRO-443", "lab-order-trap")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_dossier("CASE-METRO-443", FIX / "lab-order-trap.json", CAT)
    assert got["integrity_findings"] == ref["integrity_findings"]
    assert got["summary"]["chronology_violation"] >= 1


def test_alias_collision_trap_detected() -> None:
    """Verify duplicate court_alias across evidence ids emits alias_collision."""
    wipe()
    out = run_pipeline("CASE-METRO-444", "alias-collision-trap")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_dossier("CASE-METRO-444", FIX / "alias-collision-trap.json", CAT)
    assert got["summary"]["alias_collision"] == ref["summary"]["alias_collision"] >= 1


def test_lineage_gap_trap_detected() -> None:
    """Verify missing custody hop emits lineage_gap chain finding."""
    wipe()
    out = run_pipeline("CASE-METRO-445", "lineage-gap-trap")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_dossier("CASE-METRO-445", FIX / "lineage-gap-trap.json", CAT)
    assert got["summary"]["lineage_gap"] == ref["summary"]["lineage_gap"] == 1


def test_metro_lineage_edges_sorted_by_epoch() -> None:
    """Verify lineage edges for metro bundle follow chronological sequence."""
    wipe()
    out = run_pipeline("CASE-METRO-441", "metro-gun-chain")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_dossier("CASE-METRO-441", FIX / "metro-gun-chain.json", CAT)
    assert got["lineage_edges"] == ref["lineage_edges"]
    epochs = [e["event_epoch_ms"] for e in got["lineage_edges"]]
    assert epochs == sorted(epochs)


def test_officer_ids_preserve_casing_in_vault() -> None:
    """Verify officer identifiers keep bundle casing per custody-transfer-log-format.md."""
    wipe()
    run_pipeline("CASE-METRO-441", "metro-gun-chain")
    snap = json.loads((APP / "var" / "custody-vault.json").read_text(encoding="utf-8"))
    officers = {t["from_officer_id"] for t in snap["transfers"]} | {
        t["to_officer_id"] for t in snap["transfers"]
    }
    assert "OFF-Hart" in officers or "OFF-Reed" in officers


def test_custody_digest_is_64_char_hex() -> None:
    """Verify custody_digest is lowercase 64-char hex per dossier-output-schema.md."""
    wipe()
    out = run_pipeline("CASE-METRO-441", "metro-gun-chain")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert len(got["custody_digest"]) == 64
    assert got["custody_digest"].islower()


def test_chain_findings_sorted_by_evidence_then_code() -> None:
    """Verify chain findings sort by evidence_id then code."""
    wipe()
    out = run_pipeline("CASE-METRO-444", "alias-collision-trap")
    got = json.loads(out.read_text(encoding="utf-8"))
    pairs = [(b["evidence_id"], b["code"]) for b in got["integrity_findings"]]
    assert pairs == sorted(pairs)


def test_metro_bundle_reports_all_intact() -> None:
    """Verify intact metro-gun-chain reports zero custody violations in summary."""
    wipe()
    out = run_pipeline("CASE-METRO-441", "metro-gun-chain")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["summary"]["defect_items"] == 0
    assert got["summary"]["intact_items"] == 1


def test_export_output_under_app_output() -> None:
    """Verify exported dossier path resides under /app/output/."""
    wipe()
    out = run_pipeline("CASE-METRO-441", "metro-gun-chain")
    assert str(out).startswith("/app/output/")
    assert out.is_file()


def test_dossier_includes_case_and_bundle_ids() -> None:
    """Verify dossier JSON records case_id and bundle_id fields."""
    wipe()
    out = run_pipeline("CASE-METRO-441", "metro-gun-chain")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["case_id"] == "CASE-METRO-441"
    assert got["bundle_id"] == "metro-gun-chain"


def test_evidence_items_list_matches_bundle() -> None:
    """Verify evidence_items enumerates unique evidence ids from bundle transfers."""
    wipe()
    out = run_pipeline("CASE-METRO-441", "metro-gun-chain")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["evidence_items"] == ["EVD-7F2A"]


def test_summary_seal_counts_align_with_findings() -> None:
    """Verify summary seal_breaks count matches chain finding rows."""
    wipe()
    out = run_pipeline("CASE-METRO-442", "seal-break-trap")
    got = json.loads(out.read_text(encoding="utf-8"))
    seal_rows = sum(1 for b in got["integrity_findings"] if b["code"] == "seal_break")
    assert got["summary"]["seal_breaks"] == seal_rows
