"""Playfield rulecard matrix across reject levels."""

from __future__ import annotations

from pathlib import Path

from geobox_authority import load_level, reference_evaluate
from geobox_cli import drive_score_round, wipe_runtime


def _check(level: str, run_id: str, *, require_empty_admit: bool = False) -> None:
    wipe_runtime()
    atlas = drive_score_round(level, run_id)
    ref = reference_evaluate(
        load_level(Path(f"/app/fixtures/levels/{level}/inventory.json"))
    )
    assert [r["doc_id"] for r in atlas["admitted"]] == [
        r["doc_id"] for r in ref["admitted"]
    ]
    assert {r["doc_id"]: r["deny_reason"] for r in atlas["denied"]} == {
        r["doc_id"]: r["deny_reason"] for r in ref["denied"]
    }
    if require_empty_admit:
        assert atlas["admitted_count"] == 0
        assert atlas["denied_count"] >= 1
        assert Path("/app/output/geo-filter-playtest-atlas.json").is_file()


def test_matrix_pin_hold_denies_pinned() -> None:
    """Token pin rulecard must deny documents with non-empty filter pins."""
    _check("pin-hold", "m-pin")


def test_matrix_lag_ceiling_denies_all() -> None:
    """Lag at ceiling must reject every scoring candidate and still seal."""
    _check("lag-shard", "m-lag", require_empty_admit=True)


def test_matrix_floor_quorum_denies() -> None:
    """Document floor quorum failure must deny remaining candidates and still seal."""
    _check("floor-starve", "m-floor", require_empty_admit=True)


def test_matrix_edge_inclusive_admits_corners() -> None:
    """Inclusive rectangle corners must remain admissible."""
    wipe_runtime()
    atlas = drive_score_round("edge-band", "m-edge")
    ids = {r["doc_id"] for r in atlas["admitted"]}
    assert "EDGE-SW" in ids and "EDGE-NE" in ids
    assert "EDGE-OUT" not in ids


def test_matrix_affinity_ties_by_doc_id() -> None:
    """Equal affinity must break ties by ascending doc_id under the admit cap."""
    _check("tie-affinity", "m-tie")
