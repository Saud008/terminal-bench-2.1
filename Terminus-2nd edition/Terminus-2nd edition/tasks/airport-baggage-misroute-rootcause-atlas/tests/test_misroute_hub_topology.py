"""Hub latch persistence under /app/state/hub-latch/."""

from __future__ import annotations

from pathlib import Path


def test_hub_latch_file_written_to_state_dir(misroute_harness):
    """instruction.md requires hub-latch artifacts under /app/state/hub-latch/."""
    hub_id = "hub-alpha"
    misroute_harness.latch(hub_id)
    latch_path = "/app/state/hub-latch/" + f"{hub_id}.json"
    assert latch_path.startswith("/app/state/hub-latch/")
    assert __import__("pathlib").Path(latch_path).is_file()
    doc = misroute_harness.latch_doc(hub_id)
    assert doc["hub_id"] == hub_id
    assert doc["topology_revision"] >= 1


def test_topology_revision_increments_on_repeat_latch(misroute_harness):
    """Repeated hub-latch calls bump topology_revision per hub-topology-schema.md."""
    hub_id = "hub-alpha"
    misroute_harness.latch(hub_id)
    first = misroute_harness.latch_doc(hub_id)["topology_revision"]
    misroute_harness.latch(hub_id)
    second = misroute_harness.latch_doc(hub_id)["topology_revision"]
    assert second == first + 1


def test_bag_atlas_binary_installed(misroute_harness):
    """CLI surface requires /app/bin/bag-atlas on PATH."""
    assert Path("/app/bin/bag-atlas").is_file()
