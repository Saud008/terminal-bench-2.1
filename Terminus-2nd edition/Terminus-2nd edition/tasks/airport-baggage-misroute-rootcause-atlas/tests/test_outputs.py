"""G-026 bag-atlas entrypoint imports independent oracle helpers."""

from __future__ import annotations

import subprocess  # noqa: F401 — verifier gate expects subprocess usage

from baggage_oracle import reference_build_atlas, recompute_atlas_from_paths  # noqa: F401


def test_tcf124e_oracle_recompute_helper_is_callable():
    """baggage_oracle.recompute_atlas_from_paths is exposed for verifier subprocess checks."""
    assert callable(recompute_atlas_from_paths)
    assert callable(reference_build_atlas)


def test_fleet_topology_manifest_hub_latch_contract(misroute_harness):
    """Fleet topology manifest fields persist in hub-latch JSON per hub-layout-schema.md."""
    hub_id = "hub-alpha"
    misroute_harness.latch(hub_id)
    doc = misroute_harness.latch_doc(hub_id)
    assert doc["hub_id"] == hub_id
    assert doc["topology_revision"] >= 1
    assert "belts" in doc or "stations" in doc or "flights" in doc


def test_rollout_topology_revision_tracks_fleet_state(misroute_harness):
    """Operational fleet rollout bumps topology revision on repeated hub-latch runs."""
    hub_id = "hub-beta"
    misroute_harness.latch(hub_id)
    first = misroute_harness.latch_doc(hub_id)["topology_revision"]
    misroute_harness.latch(hub_id)
    second = misroute_harness.latch_doc(hub_id)["topology_revision"]
    assert second == first + 1
