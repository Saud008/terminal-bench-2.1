"""Hidden verifier overlays for axis, corner, pin-kind, and digit traps."""

from __future__ import annotations

import os
from pathlib import Path

from geobox_authority import atlas_digest, load_level, reference_evaluate
from geobox_cli import drive_score_round, wipe_runtime

HIDDEN = "/opt/verifier-fixtures/geobox"


def _overlay(name: str, run_id: str, digits: str | None = None):
    wipe_runtime()
    env = {"TB3_LEVEL_DIR": HIDDEN}
    if digits is not None:
        env["TB3_PLAY_DIGITS"] = digits
    full = os.environ.copy()
    full.update(env)
    atlas = drive_score_round(name, run_id, env=full)
    ref = reference_evaluate(load_level(Path(f"{HIDDEN}/{name}/inventory.json")))
    width = int(digits) if digits is not None else 4
    assert atlas["atlas_digest"] == atlas_digest(ref["admitted"], digits=width)
    return atlas, ref


def test_overlay_axis_rejects_swapped_bait() -> None:
    """Axis overlay must refuse lon/lat-swapped bait documents."""
    atlas, _ = _overlay("axis-trap", "o-axis")
    assert {r["doc_id"] for r in atlas["admitted"]} == {"AXIS-OK"}


def test_overlay_inclusive_corner() -> None:
    """Inclusive overlay must admit the exact single-point window corner."""
    atlas, _ = _overlay("inclusive-trap", "o-incl")
    assert {r["doc_id"] for r in atlas["admitted"]} == {"ON-CORNER"}


def test_overlay_pin_kind_ignores_markers() -> None:
    """Pin-kind overlay must ignore shard_marker pins."""
    atlas, _ = _overlay("pin-kind-trap", "o-pk")
    denied = {r["doc_id"]: r["deny_reason"] for r in atlas["denied"]}
    assert denied.get("DOC-PINNED") == "blocked_pin"
    assert "SHARD-WITH-PIN" not in denied


def test_overlay_digits_change_atlas_digest() -> None:
    """TB3_PLAY_DIGITS must alter atlas_digest for the same admitted set."""
    a4, _ = _overlay("axis-trap", "o-d4", digits="4")
    a6, _ = _overlay("axis-trap", "o-d6", digits="6")
    assert a4["atlas_digest"] != a6["atlas_digest"]
