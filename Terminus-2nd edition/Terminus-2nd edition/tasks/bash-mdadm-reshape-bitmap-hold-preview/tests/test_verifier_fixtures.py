"""Hidden verifier overlays for bitmap-clear and multi-spare traps."""

from __future__ import annotations

from pathlib import Path

from mdreshape_harness import HIDDEN_FIXTURE_DIR, scan_compile_publish, reset_state
from mdreshape_mathlib import audit_digest, evaluate, load_scenario


def test_mdreshape_tb3_bitmap_clear_planned_allows_reshape() -> None:
    """Internal bitmap with bitmap_clear_planned true must not be blocked_bitmap."""
    reset_state()
    env = {"TB3_SCENARIO_DIR": HIDDEN_FIXTURE_DIR}
    atlas = scan_compile_publish("hidden-bitmap-clear", "t-hclear", env=env)
    inv = load_scenario(Path(f"{HIDDEN_FIXTURE_DIR}/hidden-bitmap-clear/inventory.json"))
    ref = evaluate(inv)
    assert atlas["audit_digest"] == audit_digest(
        "t-hclear", "hidden-bitmap-clear", ref["eligible"], ref["blocked"]
    )
    assert atlas["eligible_count"] == 1
    assert "md0" in {r["name"] for r in atlas["eligible"]}


def test_mdreshape_tb3_second_spare_hold_detected() -> None:
    """A held spare in any position, not only spares[0], must block the array."""
    reset_state()
    env = {"TB3_SCENARIO_DIR": HIDDEN_FIXTURE_DIR}
    atlas = scan_compile_publish("hidden-multi-spare", "t-hspare", env=env)
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("md0") == "blocked_spare_hold"
    inv = load_scenario(Path(f"{HIDDEN_FIXTURE_DIR}/hidden-multi-spare/inventory.json"))
    ref = evaluate(inv)
    assert atlas["audit_digest"] == audit_digest(
        "t-hspare", "hidden-multi-spare", ref["eligible"], ref["blocked"]
    )


def test_mdreshape_tb3_host_salt_hashes_array_names() -> None:
    """salted_name must be derived from the scenario's own host_salt field."""
    reset_state()
    env = {"TB3_SCENARIO_DIR": HIDDEN_FIXTURE_DIR}
    atlas = scan_compile_publish("hidden-bitmap-clear", "t-hsalt", env=env)
    inv = load_scenario(Path(f"{HIDDEN_FIXTURE_DIR}/hidden-bitmap-clear/inventory.json"))
    expected = next(a["salted_name"] for a in inv["arrays"] if a["name"] == "md0")
    actual = next(r["salted_name"] for r in atlas["eligible"] if r["name"] == "md0")
    assert actual == expected
    assert len(actual) == 16
