"""TB3 verifier overlay probes for hidden bags and runtime overrides."""

from __future__ import annotations

import json

from temporal_sync_oracle import (
    collapse_msg_index_collisions,
    expected_skew_atlas,
    oracle_full_pipeline,
    parse_message_stream,
    read_bag_manifest,
)


class TestVerifierOverlays:
    """Hidden fixture roots and TB3 env overrides per pytest-verifier-primitives.md."""

    def test_hidden_bag_root_flipped_slope(self, c8skew):
        """TB3_BAG_ROOT hidden tb3-flipped-slope bag matches oracle atlas."""
        bag_id = "tb3-flipped-slope"
        env = {"TB3_BAG_ROOT": "/opt/verifier-fixtures/skew-cal/bags"}
        bdir = c8skew.bag_path(bag_id, env)
        expected, _ = oracle_full_pipeline(bdir / "bag_meta.json", bdir / "messages.jsonl")
        out = c8skew.run_skew_pipeline(bag_id, env=env)
        atlas = json.loads(out.read_text(encoding="utf-8"))
        assert atlas["sync_pair_count"] == expected["sync_pair_count"]
        assert atlas["audit_digest"] == expected["audit_digest"]

    def test_sync_window_ns_env_narrows_pairs(self, c8skew):
        """TB3_SYNC_WINDOW_NS override changes sync_pair_count per oracle."""
        bag_id = "rover-alpha"
        env = {"TB3_SYNC_WINDOW_NS": "2000000"}
        bdir = c8skew.bag_path(bag_id)
        meta = read_bag_manifest(bdir / "bag_meta.json")
        meta["sync_window_ns"] = 2_000_000
        rows = collapse_msg_index_collisions(
            parse_message_stream(bdir / "messages.jsonl", meta["topic_remap"])
        )
        expected = expected_skew_atlas(meta, rows)
        out = c8skew.run_skew_pipeline(bag_id, env=env)
        atlas = json.loads(out.read_text(encoding="utf-8"))
        assert atlas["sync_pair_count"] == expected["sync_pair_count"]

    def test_reference_topic_env_changes_anchor(self, c8skew):
        """TB3_REFERENCE_TOPIC override re-anchors sync windows on /imu/data."""
        bag_id = "rover-alpha"
        bdir = c8skew.bag_path(bag_id)
        meta = read_bag_manifest(bdir / "bag_meta.json")
        rows = collapse_msg_index_collisions(
            parse_message_stream(bdir / "messages.jsonl", meta["topic_remap"])
        )
        alt = "/imu/data"
        env = {"TB3_REFERENCE_TOPIC": alt}
        meta_alt = dict(meta)
        meta_alt["reference_topic"] = alt
        expected = expected_skew_atlas(meta_alt, rows)
        out = c8skew.run_skew_pipeline(bag_id, env=env)
        atlas = json.loads(out.read_text(encoding="utf-8"))
        assert atlas["sync_pair_count"] == expected["sync_pair_count"]
