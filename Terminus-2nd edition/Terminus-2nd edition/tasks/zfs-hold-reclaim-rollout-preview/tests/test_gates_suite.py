"""Public fixture gate and reclaim-order suite."""

from __future__ import annotations

from pathlib import Path

from zfshold_cli_support import load_compile_publish, reset_state
from zfshold_contract_math import audit_digest, evaluate, load_scenario


def _check(scenario: str, run_id: str) -> None:
    reset_state()
    atlas = load_compile_publish(scenario, run_id)
    inv = load_scenario(Path(f"/app/fixtures/scenarios/{scenario}/inventory.json"))
    ref = evaluate(inv)
    assert atlas["eligible_count"] == ref["eligible_count"]
    assert {r["name"]: r["block_reason"] for r in atlas["blocked"]} == {
        r["name"]: r["block_reason"] for r in ref["blocked"]
    }
    assert [r["name"] for r in sorted(atlas["eligible"], key=lambda r: r["reclaim_rank"])] == [
        r["name"] for r in ref["eligible"]
    ]
    assert atlas["audit_digest"] == audit_digest(ref["eligible"])


def test_clone_blocks_origin() -> None:
    """clone_of must block the origin snapshot while leaving sibling snaps eligible."""
    _check("clone-blocks-origin", "t-clone")
    reset_state()
    atlas = load_compile_publish("clone-blocks-origin", "t-clone-2")
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("tank/db@origin") == "blocked_clone"
    assert "tank/db@other" in {r["name"] for r in atlas["eligible"]}


def test_bookmark_target() -> None:
    """Bookmark target field must block the referenced snapshot, not the bookmark name."""
    _check("bookmark-target", "t-book")
    reset_state()
    atlas = load_compile_publish("bookmark-target", "t-book-2")
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("tank/web@marked") == "blocked_bookmark"
    assert "tank/web#bk1" not in blocked


def test_nested_depth_order() -> None:
    """Eligible ranks must follow depth desc then creation_txg asc then name."""
    _check("nested-depth-order", "t-depth")
    reset_state()
    atlas = load_compile_publish("nested-depth-order", "t-depth-2")
    names = [r["name"] for r in sorted(atlas["eligible"], key=lambda r: r["reclaim_rank"])]
    assert names == [
        "tank/a/b@deep-early",
        "tank/a/b@deep-mid",
        "tank/a@shallow-early",
        "tank/a@shallow-late",
    ]


def test_pool_floor_tight_equality_blocks_all() -> None:
    """free_pct equal to floor_pct must block every snapshot with blocked_pool_floor."""
    _check("pool-floor-tight", "t-floor")
    reset_state()
    atlas = load_compile_publish("pool-floor-tight", "t-floor-2")
    assert atlas["eligible_count"] == 0
    assert atlas["blocked_count"] == 2
    assert all(r["block_reason"] == "blocked_pool_floor" for r in atlas["blocked"])
