"""Fleet-wide reconnect rank: criticality ascending then mac ascending, and reason precedence."""

from __future__ import annotations

from pathlib import Path

from fleet_cutover_harness import run_cutover_preview, wipe_run_state
from bond_eligibility_oracle import evaluate_fleet, load_fleet_scenario


def test_rank_orders_by_criticality_then_mac_across_two_adapters() -> None:
    """Devices on different adapters must interleave by criticality then mac, not by adapter."""
    wipe_run_state()
    atlas = run_cutover_preview("cutover-order", "rank-cross-adapter")
    macs = [r["mac"] for r in atlas["eligible"]]
    assert macs == ["AA:00:00:00:00:01", "CC:00:00:00:00:03", "BB:00:00:00:00:02"]
    ranks = [r["rank"] for r in atlas["eligible"]]
    assert ranks == [1, 2, 3]


def test_reason_precedence_prefers_pairing_over_reconnect_storm() -> None:
    """When two gates would both trip, pairing_required must win over reconnect_storm."""
    inv = load_fleet_scenario(Path("/app/fixtures/scenarios/pairing-mismatch/inventory.json"))
    inv["adapters"][0]["devices"][0]["battery_probes_ms"] = [0, 600, 1200, 1800]
    ref = evaluate_fleet(inv)
    reasons = {r["mac"]: r["reason"] for r in ref["ineligible"]}
    assert reasons["AA:BB:CC:DD:EE:02"] == "ineligible_pairing_required"


def test_reason_precedence_prefers_resume_over_power_sequence() -> None:
    """When resume and power-sequence would both trip, resume_armed must win."""
    inv = load_fleet_scenario(Path("/app/fixtures/scenarios/resume-armed-block/inventory.json"))
    inv["adapters"][0]["power_plan"] = "off_first"
    ref = evaluate_fleet(inv)
    reasons = {r["mac"]: r["reason"] for r in ref["ineligible"]}
    assert reasons["AA:BB:CC:DD:EE:03"] == "ineligible_resume_armed"
