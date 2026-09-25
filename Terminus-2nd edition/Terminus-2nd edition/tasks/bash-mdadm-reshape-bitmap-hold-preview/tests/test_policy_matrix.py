"""Public fixture gate and reshape-order suite."""

from __future__ import annotations

from pathlib import Path

from mdreshape_harness import scan_compile_publish, reset_state
from mdreshape_mathlib import audit_digest, evaluate, load_scenario


def _check(scenario: str, run_id: str) -> dict:
    reset_state()
    atlas = scan_compile_publish(scenario, run_id)
    inv = load_scenario(Path(f"/app/fixtures/scenarios/{scenario}/inventory.json"))
    ref = evaluate(inv)
    assert atlas["eligible_count"] == ref["eligible_count"]
    assert atlas["blocked_count"] == ref["blocked_count"]
    assert {r["name"]: r["block_reason"] for r in atlas["blocked"]} == {
        r["name"]: r["block_reason"] for r in ref["blocked"]
    }
    assert [r["name"] for r in atlas["eligible"]] == [r["name"] for r in ref["eligible"]]
    assert atlas["audit_digest"] == audit_digest(run_id, scenario, ref["eligible"], ref["blocked"])
    return atlas


def test_mdreshape_internal_bitmap_freezes_array() -> None:
    """Internal bitmap without a planned clear must block with blocked_bitmap."""
    atlas = _check("bitmap-internal", "t-bitmap")
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("md0") == "blocked_bitmap"


def test_mdreshape_held_spare_slot_freezes_array() -> None:
    """A held spare device must block the array that lists it."""
    atlas = _check("spare-hold-block", "t-spare")
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("md0") == "blocked_spare_hold"


def test_mdreshape_raid5_under_min_active_disks() -> None:
    """A raid5 array below its degraded floor must block with blocked_degraded."""
    atlas = _check("degraded-raid5", "t-degraded")
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("md0") == "blocked_degraded"


def test_mdreshape_raid6_to_raid5_path_rejected() -> None:
    """raid6 to raid5 is not a legal reshape path and must be blocked."""
    atlas = _check("illegal-path", "t-illegal")
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("md0") == "blocked_illegal_path"


def test_mdreshape_hours_over_budget_freezes_array() -> None:
    """Only the array strictly over the window budget is blocked_window."""
    atlas = _check("window-tight", "t-window")
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("md0") == "blocked_window"
    assert "md1" in {r["name"] for r in atlas["eligible"]}


def test_mdreshape_ranks_by_criticality_then_array_name() -> None:
    """Eligible arrays must be ranked by criticality ascending then name ascending."""
    atlas = _check("order-criticality", "t-order")
    names = [r["name"] for r in atlas["eligible"]]
    assert names == ["md0", "md1", "md3", "md2"]
