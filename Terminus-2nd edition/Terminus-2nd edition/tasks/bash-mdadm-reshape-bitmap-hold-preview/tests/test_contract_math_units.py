"""Unit coverage for independent reference_evaluate math without the CLI."""

from __future__ import annotations

from pathlib import Path

from mdreshape_mathlib import (
    reference_audit_digest,
    reference_evaluate,
    load_scenario,
    salted_name,
)


def test_oracle_math_basic_raid5_to_raid6_ok() -> None:
    """reference_evaluate must keep a clean raid5 to raid6 array eligible."""
    inv = load_scenario(Path("/app/fixtures/scenarios/basic-reshape/inventory.json"))
    ref = reference_evaluate(inv)
    assert ref["eligible_count"] == 1
    assert ref["blocked_count"] == 0
    assert reference_audit_digest("t-unit", "basic-reshape", ref["eligible"], ref["blocked"])


def test_oracle_math_internal_bitmap_reason() -> None:
    """reference_evaluate must block internal bitmaps without a planned clear."""
    inv = load_scenario(Path("/app/fixtures/scenarios/bitmap-internal/inventory.json"))
    ref = reference_evaluate(inv)
    blocked = {r["name"]: r["block_reason"] for r in ref["blocked"]}
    assert blocked["md0"] == "blocked_bitmap"


def test_oracle_math_raid5_floor_reason() -> None:
    """reference_evaluate must apply the raid5 minimum of 3 active disks."""
    inv = load_scenario(Path("/app/fixtures/scenarios/degraded-raid5/inventory.json"))
    ref = reference_evaluate(inv)
    blocked = {r["name"]: r["block_reason"] for r in ref["blocked"]}
    assert blocked["md0"] == "blocked_degraded"


def test_oracle_math_illegal_raid_path_reason() -> None:
    """reference_evaluate must reject raid6 to raid5 as an illegal path."""
    inv = load_scenario(Path("/app/fixtures/scenarios/illegal-path/inventory.json"))
    ref = reference_evaluate(inv)
    blocked = {r["name"]: r["block_reason"] for r in ref["blocked"]}
    assert blocked["md0"] == "blocked_illegal_path"


def test_oracle_math_equal_hours_still_eligible() -> None:
    """reference_evaluate must treat estimated_hours == window_hours as fitting."""
    inv = load_scenario(Path("/app/fixtures/scenarios/window-tight/inventory.json"))
    ref = reference_evaluate(inv)
    blocked = {r["name"]: r["block_reason"] for r in ref["blocked"]}
    eligible_names = {r["name"] for r in ref["eligible"]}
    assert blocked["md0"] == "blocked_window"
    assert "md1" in eligible_names


def test_oracle_math_bitmap_reason_outranks_window() -> None:
    """Bitmap block reason must win priority over a window overrun on the same array."""
    inv = load_scenario(Path("/app/fixtures/scenarios/bitmap-internal/inventory.json"))
    inv["window_hours"] = 0
    ref = reference_evaluate(inv)
    blocked = {r["name"]: r["block_reason"] for r in ref["blocked"]}
    assert blocked["md0"] == "blocked_bitmap"


def test_oracle_math_salted_array_name_hex16() -> None:
    """salted_name must be deterministic for the same host_salt and array name."""
    first = salted_name("alpha", "md0")
    second = salted_name("alpha", "md0")
    different_salt = salted_name("beta", "md0")
    assert first == second
    assert first != different_salt
    assert len(first) == 16
    int(first, 16)
