"""Synchronization windows, drift regression, and skew atlas emission."""

from __future__ import annotations

import json

import pytest

from temporal_sync_oracle import (
    build_sync_windows,
    collapse_msg_index_collisions,
    oracle_full_pipeline,
    parse_message_stream,
    read_bag_manifest,
)


class TestSkewAtlasPublish:
    """emit-skew and match-sync vs sync-window-matching.md and drift-regression-contract.md."""

    @pytest.mark.parametrize(
        "bag_id,field",
        [
            ("rover-alpha", "sync_pair_count"),
            ("rover-gamma", "drop_count"),
            ("rover-beta", "audit_digest"),
        ],
    )
    def test_scalar_atlas_field_matches_oracle(self, c8skew, bag_id: str, field: str):
        """Selected atlas scalar fields match independent temporal_sync_oracle."""
        bdir = c8skew.bag_path(bag_id)
        expected, _ = oracle_full_pipeline(bdir / "bag_meta.json", bdir / "messages.jsonl")
        out = c8skew.run_skew_pipeline(bag_id)
        atlas = json.loads(out.read_text(encoding="utf-8"))
        assert atlas[field] == expected[field]

    def test_drift_regression_rows_rover_alpha(self, c8skew):
        """Per-topic drift slopes and intercepts match centered least-squares oracle."""
        bag_id = "rover-alpha"
        bdir = c8skew.bag_path(bag_id)
        expected, _ = oracle_full_pipeline(bdir / "bag_meta.json", bdir / "messages.jsonl")
        out = c8skew.run_skew_pipeline(bag_id)
        atlas = json.loads(out.read_text(encoding="utf-8"))
        assert len(atlas["drift_rows"]) == len(expected["drift_rows"])
        for got, exp in zip(atlas["drift_rows"], expected["drift_rows"]):
            assert got["topic"] == exp["topic"]
            assert abs(got["slope"] - exp["slope"]) < 1e-4
            assert abs(got["intercept_ns"] - exp["intercept_ns"]) < 1.0

    def test_end_to_end_rover_gamma_digest(self, c8skew):
        """Full rover-gamma pipeline matches oracle sync_pair_count and audit_digest."""
        bag_id = "rover-gamma"
        bdir = c8skew.bag_path(bag_id)
        expected, _ = oracle_full_pipeline(bdir / "bag_meta.json", bdir / "messages.jsonl")
        out = c8skew.run_skew_pipeline(bag_id)
        atlas = json.loads(out.read_text(encoding="utf-8"))
        assert atlas["sync_pair_count"] == expected["sync_pair_count"]
        assert atlas["audit_digest"] == expected["audit_digest"]

    def test_end_to_end_rover_delta_drop_count(self, c8skew):
        """rover-delta drop_count matches stream gap ledger oracle."""
        bag_id = "rover-delta"
        bdir = c8skew.bag_path(bag_id)
        expected, _ = oracle_full_pipeline(bdir / "bag_meta.json", bdir / "messages.jsonl")
        out = c8skew.run_skew_pipeline(bag_id)
        atlas = json.loads(out.read_text(encoding="utf-8"))
        assert atlas["drop_count"] == expected["drop_count"]

    def test_timeline_ledger_norm_snapshot_rover_alpha(self, c8skew):
        """Ledger snapshot: timeline-ledger rows match oracle sort order after norm-stream."""
        bag_id = "rover-alpha"
        bdir = c8skew.bag_path(bag_id)
        meta = read_bag_manifest(bdir / "bag_meta.json")
        expected = collapse_msg_index_collisions(
            parse_message_stream(bdir / "messages.jsonl", meta["topic_remap"])
        )
        c8skew.run_skew_pipeline(bag_id)
        staged = c8skew.read_timeline_ledger_rows(bag_id)
        assert [(r["header_stamp_ns"], r["topic"]) for r in staged] == [
            (r["header_stamp_ns"], r["topic"]) for r in expected
        ]

    def test_reference_anchor_not_global_minimum(self, c8skew):
        """Sync pairs anchor on reference topic stamps, not global minimum header."""
        bag_id = "rover-delta"
        bdir = c8skew.bag_path(bag_id)
        meta = read_bag_manifest(bdir / "bag_meta.json")
        rows = collapse_msg_index_collisions(
            parse_message_stream(bdir / "messages.jsonl", meta["topic_remap"])
        )
        pairs = build_sync_windows(rows, meta["reference_topic"], meta["sync_window_ns"])
        assert pairs
        assert any(p["ref_stamp_ns"] > rows[0]["header_stamp_ns"] for p in pairs)
