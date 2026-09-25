"""Rollout atlas shape and audit_digest reproducibility across independent math."""

from __future__ import annotations

from pathlib import Path

from fleet_cutover_harness import run_cutover_preview, wipe_run_state
from bond_eligibility_oracle import (
    compute_audit_digest,
    evaluate_fleet,
    load_fleet_scenario,
    reference_audit_digest,
)


def test_atlas_schema_carries_required_top_level_fields() -> None:
    """Published atlas must expose schema_version and every documented count field."""
    wipe_run_state()
    atlas = run_cutover_preview("basic-reconnect", "digest-shape")
    for field in (
        "schema_version",
        "run_id",
        "scenario",
        "fleet",
        "eligible",
        "ineligible",
        "eligible_count",
        "ineligible_count",
        "audit_digest",
    ):
        assert field in atlas
    assert atlas["schema_version"] == 1
    assert len(atlas["audit_digest"]) == 64
    int(atlas["audit_digest"], 16)


def test_audit_digest_matches_sorted_line_formula() -> None:
    """audit_digest must equal sha256 of the sorted adapter|mac|eligible|reason|rank lines."""
    wipe_run_state()
    atlas = run_cutover_preview("cutover-order", "digest-cutover")
    inv = load_fleet_scenario(Path("/app/fixtures/scenarios/cutover-order/inventory.json"))
    ref = evaluate_fleet(inv)
    assert atlas["audit_digest"] == reference_audit_digest(ref["eligible"], ref["ineligible"])
    assert reference_audit_digest(ref["eligible"], ref["ineligible"]) == compute_audit_digest(
        ref["eligible"], ref["ineligible"]
    )

def test_audit_digest_is_stable_across_repeated_publish_calls() -> None:
    """Publishing twice against the same reconnect ledger must reproduce the same digest."""
    wipe_run_state()
    first = run_cutover_preview("basic-reconnect", "digest-repeat")
    second = run_cutover_preview("basic-reconnect", "digest-repeat")
    assert first["audit_digest"] == second["audit_digest"]


def test_audit_digest_is_order_independent_of_device_iteration() -> None:
    """Two fleets whose only difference is device order must still hash identically once sorted."""
    forward = evaluate_fleet(
        load_fleet_scenario(Path("/app/fixtures/scenarios/cutover-order/inventory.json"))
    )
    reversed_inv = load_fleet_scenario(Path("/app/fixtures/scenarios/cutover-order/inventory.json"))
    reversed_inv["adapters"] = list(reversed(reversed_inv["adapters"]))
    for adapter in reversed_inv["adapters"]:
        adapter["devices"] = list(reversed(adapter["devices"]))
    backward = evaluate_fleet(reversed_inv)
    assert compute_audit_digest(forward["eligible"], forward["ineligible"]) == compute_audit_digest(
        backward["eligible"], backward["ineligible"]
    )
