"""TB3 hidden overlays and decoy isolation."""

from __future__ import annotations

import json

from baggage_oracle import recompute_atlas_from_paths


def test_tb3_outage_half_open_end_boundary(misroute_harness):
    """TB3 hub scan at outage end_minute is not suppressed per outage-window-contract.md."""
    hub_id = "tb3-outage-edge"
    env = {"TB3_HUB_ROOT": "/opt/verifier-fixtures/bag-atlas/hubs"}
    hdir = misroute_harness.hub_dir(hub_id, env)
    expected, _ = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl")
    atlas = json.loads(misroute_harness.full_pipeline(hub_id, env=env).read_text(encoding="utf-8"))
    assert atlas["suppressed_count"] == expected["suppressed_count"]


def test_tb3_mct_minutes_env_override(misroute_harness):
    """TB3_MCT_MINUTES lowers connection threshold for verifier-only hub rerun."""
    hub_id = "hub-beta"
    env = {"TB3_MCT_MINUTES": "5"}
    hdir = misroute_harness.hub_dir(hub_id)
    expected, _ = recompute_atlas_from_paths(hdir / "hub_topology.json", hdir / "scans.jsonl", mct_override=5)
    atlas = json.loads(misroute_harness.full_pipeline(hub_id, env=env).read_text(encoding="utf-8"))
    assert atlas["misroute_count"] == expected["misroute_count"]


def test_weight_forecast_decoy_not_wired_to_cli(misroute_harness):
    """weight_decoy module stays off hub-latch, seq-scans, route-belts, emit-rootcause hot path."""
    main_rs = open("/app/src/a7_main.rs", encoding="utf-8").read()
    assert "weight_decoy" not in main_rs
    assert "estimate_weight_kg" in open("/app/weight_decoy/forecast.rs", encoding="utf-8").read()
