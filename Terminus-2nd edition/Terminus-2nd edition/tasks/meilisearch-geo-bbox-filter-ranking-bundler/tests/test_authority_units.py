"""Authority helper unit checks for haversine, lag, and digest stability."""

from __future__ import annotations

from geobox_authority import atlas_digest, haversine_km, reference_evaluate


def test_haversine_identity() -> None:
    """Identical coordinates must yield zero haversine distance."""
    assert haversine_km(1.5, 2.5, 1.5, 2.5) == 0.0


def test_lag_equality_blocks() -> None:
    """Lag equal to ceiling is not strictly less and must deny all docs."""
    inv = {
        "lag_ms": 40,
        "lag_ceiling_ms": 40,
        "doc_floor": 1,
        "max_admit": 3,
        "window": {"min_lon": 0, "min_lat": 0, "max_lon": 2, "max_lat": 2},
        "focus": {"lon": 1, "lat": 1},
        "documents": [
            {
                "doc_id": "X",
                "kind": "document",
                "lon": 1,
                "lat": 1,
                "filter_pins": [],
                "capture_seq": 1,
            }
        ],
    }
    ref = reference_evaluate(inv)
    assert ref["admitted_count"] == 0
    assert ref["denied"][0]["deny_reason"] == "blocked_replica_lag"


def test_digest_repeatable() -> None:
    """Witness digest helper must be deterministic for a fixed admitted list."""
    rows = [
        {"doc_id": "P", "affinity": 0.9, "admit_rank": 1},
        {"doc_id": "Q", "affinity": 0.1, "admit_rank": 2},
    ]
    assert atlas_digest(rows, digits=4) == atlas_digest(rows, digits=4)
