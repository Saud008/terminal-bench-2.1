"""Unit coverage for independent reference_evaluate math without CLI."""

from __future__ import annotations

from pathlib import Path

from zfshold_contract_math import (
    reference_audit_digest,
    reference_evaluate,
    load_scenario,
)


def test_reference_evaluate_basic_hold() -> None:
    """reference_evaluate must block held snaps and keep free snaps eligible."""
    inv = load_scenario(Path("/app/fixtures/scenarios/basic-hold/inventory.json"))
    ref = reference_evaluate(inv)
    assert ref["eligible_count"] == 1
    assert ref["blocked"][0]["block_reason"] == "blocked_hold"
    assert reference_audit_digest(ref["eligible"])


def test_reference_evaluate_clone_origin() -> None:
    """reference_evaluate must mark clone origins blocked_clone."""
    inv = load_scenario(Path("/app/fixtures/scenarios/clone-blocks-origin/inventory.json"))
    ref = reference_evaluate(inv)
    blocked = {r["name"]: r["block_reason"] for r in ref["blocked"]}
    assert blocked["tank/db@origin"] == "blocked_clone"


def test_reference_evaluate_bookmark_target() -> None:
    """reference_evaluate must use bookmark target not bookmark name."""
    inv = load_scenario(Path("/app/fixtures/scenarios/bookmark-target/inventory.json"))
    ref = reference_evaluate(inv)
    names = {r["name"] for r in ref["blocked"]}
    assert "tank/web@marked" in names
    assert "tank/web#bk1" not in names


def test_reference_evaluate_depth_order() -> None:
    """reference_evaluate reclaim ranks must prefer deeper snapshots."""
    inv = load_scenario(Path("/app/fixtures/scenarios/nested-depth-order/inventory.json"))
    ref = reference_evaluate(inv)
    names = [r["name"] for r in ref["eligible"]]
    assert names[0].startswith("tank/a/b@")


def test_reference_evaluate_pool_floor_equality() -> None:
    """reference_evaluate must treat free_pct == floor_pct as floor failure."""
    inv = load_scenario(Path("/app/fixtures/scenarios/pool-floor-tight/inventory.json"))
    ref = reference_evaluate(inv)
    assert ref["eligible_count"] == 0
    assert all(r["block_reason"] == "blocked_pool_floor" for r in ref["blocked"])


def test_reference_evaluate_hold_priority_over_floor() -> None:
    """Held snapshots keep blocked_hold even when floor would also apply."""
    inv = load_scenario(Path("/app/fixtures/scenarios/basic-hold/inventory.json"))
    inv["free_pct"] = inv["floor_pct"]
    ref = reference_evaluate(inv)
    blocked = {r["name"]: r["block_reason"] for r in ref["blocked"]}
    assert blocked["tank/app@keep"] == "blocked_hold"
    assert blocked["tank/app@free"] == "blocked_pool_floor"
