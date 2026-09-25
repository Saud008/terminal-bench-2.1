"""Reference math unit probes for evac oracle."""

from __future__ import annotations

from evac_independent import (
    classify_severity,
    overlap_ratio,
    point_in_polygon,
    polygons_intersect,
    shortest_path_km,
)


def test_point_in_square():
    """Ray-cast point-in-polygon follows coordinate-geometry-contract winding rules."""
    poly = [{"x": 0, "y": 0}, {"x": 2, "y": 0}, {"x": 2, "y": 2}, {"x": 0, "y": 2}]
    assert point_in_polygon((1.0, 1.0), poly)
    assert not point_in_polygon((3.0, 3.0), poly)


def test_concave_no_intersection():
    """Concave zone footprints must not intersect when bbox overlap alone would be positive."""
    zone = [{"x": 0, "y": 0}, {"x": 4, "y": 0}, {"x": 4, "y": 1}, {"x": 1, "y": 1}, {"x": 1, "y": 4}, {"x": 0, "y": 4}]
    fire = [{"x": 3.4, "y": 3.4}, {"x": 3.9, "y": 3.4}, {"x": 3.9, "y": 3.9}, {"x": 3.4, "y": 3.9}]
    assert not polygons_intersect(zone, fire)
    assert overlap_ratio(zone, fire) == 0.0


def test_closed_edge_skipped_in_bfs():
    """Routing must ignore closed segments when computing shortest paths."""
    roads = {
        "nodes": [{"id": "A", "x": 0, "y": 0}, {"id": "B", "x": 2, "y": 0}, {"id": "C", "x": 4, "y": 0}],
        "edges": [{"from": "A", "to": "B", "km": 2, "closed": True}, {"from": "B", "to": "C", "km": 2, "closed": False}],
    }
    assert shortest_path_km(roads, (0.0, 0.0), (4.0, 0.0)) is None


def test_classify_severity_thresholds():
    """Severity tiers must follow numeric overlap thresholds in severity-precedence-contract."""
    policy = {"immediate_overlap": 0.45, "urgent_overlap": 0.12}
    assert classify_severity(0.5, policy) == "IMMEDIATE"
    assert classify_severity(0.2, policy) == "URGENT"
    assert classify_severity(0.05, policy) == "ADVISORY"
    assert classify_severity(0.0, policy) == "NONE"


def test_overlap_positive_when_intersects():
    """Overlap ratio must be positive when fire perimeter and zone polygons intersect."""
    zone = [{"x": 0, "y": 0}, {"x": 2, "y": 0}, {"x": 2, "y": 2}, {"x": 0, "y": 2}]
    fire = [{"x": 1, "y": 1}, {"x": 3, "y": 1}, {"x": 3, "y": 3}, {"x": 1, "y": 3}]
    assert polygons_intersect(zone, fire)
    assert overlap_ratio(zone, fire) > 0.0
