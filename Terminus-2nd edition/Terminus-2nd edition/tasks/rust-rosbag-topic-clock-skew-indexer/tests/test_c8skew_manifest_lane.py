"""Manifest latch and manifest-latch persistence probes."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import SKEW_CAL_BIN
from temporal_sync_oracle import read_bag_manifest

MANIFEST_LATCH_ROOT = "/app/state/manifest-latch/"
OUTPUT_ROOT = "/app/output/."


class TestManifestLatchLane:
    """latch-meta contract checks against manifest-latch-schema.md."""

    @pytest.mark.parametrize("bag_id", ["rover-alpha", "rover-beta"])
    def test_topic_remap_roundtrip(self, c8skew, bag_id: str):
        """topic_remap from bag_meta.json must survive manifest latch."""
        meta_path = c8skew.bag_path(bag_id) / "bag_meta.json"
        proc = c8skew.shell(
            [str(SKEW_CAL_BIN), "latch-meta", "--bag-id", bag_id, "--meta", str(meta_path)]
        )
        assert proc.returncode == 0, proc.stderr
        latch_doc = c8skew.read_manifest_latch(bag_id)
        raw = read_bag_manifest(meta_path)
        assert latch_doc["topic_remap"] == raw["topic_remap"]

    def test_manifest_revision_monotonic_on_repeat(self, c8skew):
        """Repeated latch-meta calls bump manifest_revision."""
        bag_id = "rover-beta"
        meta_path = c8skew.bag_path(bag_id) / "bag_meta.json"
        c8skew.shell([str(SKEW_CAL_BIN), "latch-meta", "--bag-id", bag_id, "--meta", str(meta_path)])
        c8skew.shell([str(SKEW_CAL_BIN), "latch-meta", "--bag-id", bag_id, "--meta", str(meta_path)])
        latch_doc = c8skew.read_manifest_latch(bag_id)
        assert latch_doc["manifest_revision"] >= 2

    def test_sync_lattice_header_carries_reference_topic(self, c8skew):
        """match-sync header records reference_topic from staged manifest."""
        bag_id = "rover-beta"
        c8skew.run_skew_pipeline(bag_id)
        hdr = c8skew.read_sync_header(bag_id)
        assert hdr["reference_topic"] == "/clock/anchor"

    def test_manifest_latch_artifact_path(self, c8skew):
        """Manifest latch JSON persists under /app/state/manifest-latch/."""
        bag_id = "rover-alpha"
        meta_path = c8skew.bag_path(bag_id) / "bag_meta.json"
        proc = c8skew.shell(
            [str(SKEW_CAL_BIN), "latch-meta", "--bag-id", bag_id, "--meta", str(meta_path)]
        )
        assert proc.returncode == 0, proc.stderr
        latch_path = Path(MANIFEST_LATCH_ROOT) / f"{bag_id}.json"
        assert latch_path.is_file()

    def test_skew_atlas_output_path(self, c8skew):
        """emit-skew writes skew atlas JSON under /app/output/."""
        bag_id = "rover-alpha"
        out = c8skew.run_skew_pipeline(bag_id)
        assert out.parent == Path(OUTPUT_ROOT.rstrip("."))
        assert out.name.endswith("-skew-atlas.json")
