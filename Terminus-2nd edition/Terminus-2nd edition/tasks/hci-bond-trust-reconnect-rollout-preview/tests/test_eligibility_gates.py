"""One gate, one public scenario: pairing, resume, power, storm, and GATT catalog math."""

from __future__ import annotations

from pathlib import Path

from fleet_cutover_harness import run_cutover_preview, wipe_run_state
from bond_eligibility_oracle import compute_audit_digest, evaluate_fleet, load_fleet_scenario


def _run_and_verify(scenario: str, run_id: str) -> dict:
    wipe_run_state()
    atlas = run_cutover_preview(scenario, run_id)
    inv = load_fleet_scenario(Path(f"/app/fixtures/scenarios/{scenario}/inventory.json"))
    ref = evaluate_fleet(inv)
    assert atlas["eligible_count"] == ref["eligible_count"]
    assert atlas["ineligible_count"] == ref["ineligible_count"]
    assert {r["mac"]: r["reason"] for r in atlas["ineligible"]} == {
        r["mac"]: r["reason"] for r in ref["ineligible"]
    }
    assert [r["mac"] for r in atlas["eligible"]] == [r["mac"] for r in ref["eligible"]]
    assert atlas["audit_digest"] == compute_audit_digest(ref["eligible"], ref["ineligible"])
    return atlas


def test_address_type_drift_without_confirmation_is_ineligible() -> None:
    """A device whose live address type drifted from the bonded type without confirmation drops out."""
    atlas = _run_and_verify("pairing-mismatch", "gate-pairing")
    reasons = {r["mac"]: r["reason"] for r in atlas["ineligible"]}
    assert reasons.get("AA:BB:CC:DD:EE:02") == "ineligible_pairing_required"


def test_stale_resume_token_without_clear_flag_is_ineligible() -> None:
    """An armed resume slot with resume_cleared false must drop the device out of rollout."""
    atlas = _run_and_verify("resume-armed-block", "gate-resume")
    reasons = {r["mac"]: r["reason"] for r in atlas["ineligible"]}
    assert reasons.get("AA:BB:CC:DD:EE:03") == "ineligible_resume_armed"


def test_off_first_adapter_without_disconnect_flag_is_ineligible() -> None:
    """An off_first power plan requires disconnect_before_power on every device it owns."""
    atlas = _run_and_verify("power-sequence-gap", "gate-power")
    reasons = {r["mac"]: r["reason"] for r in atlas["ineligible"]}
    assert reasons.get("AA:BB:CC:DD:EE:04") == "ineligible_power_sequence"


def test_debounced_probe_count_over_budget_is_ineligible() -> None:
    """Reconnect attempts strictly above the configured budget drop the device out."""
    atlas = _run_and_verify("reconnect-storm", "gate-storm")
    reasons = {r["mac"]: r["reason"] for r in atlas["ineligible"]}
    assert reasons.get("AA:BB:CC:DD:EE:05") == "ineligible_reconnect_storm"


def test_gatt_catalog_folds_mixed_case_service_uuids() -> None:
    """gatt_service_count on an eligible row must fold case-duplicate UUIDs."""
    atlas = _run_and_verify("gatt-duplicate-uuids", "gate-gatt")
    row = next(r for r in atlas["eligible"] if r["mac"] == "AA:BB:CC:DD:EE:06")
    assert row["gatt_service_count"] == 2
