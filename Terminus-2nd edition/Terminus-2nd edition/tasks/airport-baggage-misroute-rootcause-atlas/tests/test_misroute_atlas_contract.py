"""Root-cause atlas emission and route lattice contracts."""

from __future__ import annotations

import json

from baggage_oracle import recompute_atlas_from_paths, reference_route_rows_from_paths


def test_rootcause_atlas_lands_under_app_output(misroute_harness):
    """instruction.md requires atlas JSON under /app/output/ with -rootcause-atlas.json suffix."""
    hub_id = "hub-alpha"
    atlas_path = misroute_harness.full_pipeline(hub_id)
    assert "/app/output/" in str(atlas_path)
    assert str(atlas_path).startswith("/app/output/")
    assert atlas_path.name.endswith("-rootcause-atlas.json")
    assert atlas_path.is_file()


def test_misroute_histogram_matches_independent_oracle(misroute_harness):
    """cause_histogram keys follow root-cause-taxonomy.md and match baggage_oracle reference."""
    hub_id = "hub-alpha"
    hdir = misroute_harness.hub_dir(hub_id)
    expected, _ = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    atlas = json.loads(misroute_harness.full_pipeline(hub_id).read_text(encoding="utf-8"))
    assert atlas["cause_histogram"] == expected["cause_histogram"]


def test_connection_boundary_counts_mct_gap(misroute_harness):
    """hub-beta exercises minimum connection feasibility at exact MCT boundary."""
    hub_id = "hub-beta"
    hdir = misroute_harness.hub_dir(hub_id)
    expected, _ = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    atlas = json.loads(misroute_harness.full_pipeline(hub_id).read_text(encoding="utf-8"))
    assert atlas["misroute_count"] == expected["misroute_count"]


def test_outage_suppressed_rows_excluded_from_misroute_total(misroute_harness):
    """atlas-output-fields.md excludes OUTAGE_SUPPRESSED from misroute_count."""
    hub_id = "hub-gamma"
    hdir = misroute_harness.hub_dir(hub_id)
    expected, _ = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    atlas = json.loads(misroute_harness.full_pipeline(hub_id).read_text(encoding="utf-8"))
    assert atlas["suppressed_count"] == expected["suppressed_count"]
    assert atlas["misroute_count"] == expected["misroute_count"]


def test_belt_priority_selects_highest_target_flight(misroute_harness):
    """belt-route-lattice.md picks highest belt priority when belt_id collides."""
    hub_id = "hub-delta"
    hdir = misroute_harness.hub_dir(hub_id)
    _, expected_rows = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    misroute_harness.full_pipeline(hub_id)
    row = misroute_harness.route_rows(hub_id)[0]
    assert row["target_flight_id"] == expected_rows[0]["target_flight_id"]


def test_route_lattice_row_count_matches_scan_ledger(misroute_harness):
    """route-belts emits one lattice row per normalized scan row."""
    hub_id = "hub-alpha"
    hdir = misroute_harness.hub_dir(hub_id)
    _, expected_rows = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    misroute_harness.full_pipeline(hub_id)
    assert len(misroute_harness.route_rows(hub_id)) == len(expected_rows)


def test_audit_digest_matches_oracle(misroute_harness):
    """audit_digest is sha256 over sorted route rows per pytest-verifier-primitives.md."""
    hub_id = "hub-delta"
    hdir = misroute_harness.hub_dir(hub_id)
    expected, _ = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    atlas = json.loads(misroute_harness.full_pipeline(hub_id).read_text(encoding="utf-8"))
    assert atlas["audit_digest"] == expected["audit_digest"]


def test_reference_route_rows_match_lattice(misroute_harness):
    """reference_route_rows_from_paths reproduces route-belts row targets independently."""
    hub_id = "hub-delta"
    hdir = misroute_harness.hub_dir(hub_id)
    expected = reference_route_rows_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    misroute_harness.full_pipeline(hub_id)
    got = misroute_harness.route_rows(hub_id)
    assert got[0]["target_flight_id"] == expected[0]["target_flight_id"]


def test_route_row_count_scalar_in_atlas(misroute_harness):
    """route_row_count field mirrors lattice row cardinality."""
    hub_id = "hub-alpha"
    hdir = misroute_harness.hub_dir(hub_id)
    expected, _ = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    atlas = json.loads(misroute_harness.full_pipeline(hub_id).read_text(encoding="utf-8"))
    assert atlas["route_row_count"] == expected["route_row_count"]
