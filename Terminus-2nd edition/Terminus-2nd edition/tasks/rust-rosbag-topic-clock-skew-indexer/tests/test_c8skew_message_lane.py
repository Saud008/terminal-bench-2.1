"""Message stream normalization, monotonic guards, and duplicate supersession."""

from __future__ import annotations

from conftest import SKEW_CAL_BIN
from temporal_sync_oracle import (
    collapse_msg_index_collisions,
    parse_message_stream,
    read_bag_manifest,
)


class TestMessageLedgerLane:
    """norm-stream behavior vs message-stream-format.md and monotonic-stamp-contract.md."""

    def test_remap_strips_sensor_prefix_topics(self, c8skew):
        """Canonical topics like /imu/data appear after remap rules apply."""
        bag_id = "rover-alpha"
        c8skew.run_skew_pipeline(bag_id)
        topics = {row["topic"] for row in c8skew.read_timeline_ledger_rows(bag_id)}
        assert "/imu/data" in topics
        assert all(not t.startswith("/sensor/") for t in topics)

    def test_header_stamp_not_receive_stamp(self, c8skew):
        """Staged header_stamp_ns must match oracle header not receive_stamp_ns."""
        bag_id = "rover-alpha"
        bdir = c8skew.bag_path(bag_id)
        meta = read_bag_manifest(bdir / "bag_meta.json")
        expected = collapse_msg_index_collisions(
            parse_message_stream(bdir / "messages.jsonl", meta["topic_remap"])
        )
        c8skew.run_skew_pipeline(bag_id)
        staged = c8skew.read_timeline_ledger_rows(bag_id)
        assert staged[0]["header_stamp_ns"] == expected[0]["header_stamp_ns"]

    def test_timeline_ledger_global_sort_order(self, c8skew):
        """Ledger MsgRows follow (header_stamp_ns, topic) order per timeline-ledger-schema.md."""
        bag_id = "rover-alpha"
        bdir = c8skew.bag_path(bag_id)
        meta = read_bag_manifest(bdir / "bag_meta.json")
        expected = collapse_msg_index_collisions(
            parse_message_stream(bdir / "messages.jsonl", meta["topic_remap"])
        )
        c8skew.run_skew_pipeline(bag_id)
        staged = c8skew.read_timeline_ledger_rows(bag_id)
        staged_keys = [(row["header_stamp_ns"], row["topic"]) for row in staged]
        expected_keys = [(row["header_stamp_ns"], row["topic"]) for row in expected]
        assert staged_keys == expected_keys

    def test_strict_monotonic_gamma_bag(self, c8skew):
        """rover-gamma stream with equal stamps must still stage successfully when fixed."""
        bag_id = "rover-gamma"
        bdir = c8skew.bag_path(bag_id)
        c8skew.shell(
            [str(SKEW_CAL_BIN), "latch-meta", "--bag-id", bag_id, "--meta", str(bdir / "bag_meta.json")]
        )
        proc = c8skew.shell(
            [str(SKEW_CAL_BIN), "norm-stream", "--bag-id", bag_id, "--stream", str(bdir / "messages.jsonl")]
        )
        assert proc.returncode == 0, proc.stderr

    def test_duplicate_seq_keeps_latest_epoch(self, c8skew):
        """Duplicate (topic,seq) rows collapse to highest relay_pass."""
        bag_id = "rover-beta"
        bdir = c8skew.bag_path(bag_id)
        meta = read_bag_manifest(bdir / "bag_meta.json")
        oracle_rows = collapse_msg_index_collisions(
            parse_message_stream(bdir / "messages.jsonl", meta["topic_remap"])
        )
        c8skew.run_skew_pipeline(bag_id)
        staged = c8skew.read_timeline_ledger_rows(bag_id)
        imu_staged = [r for r in staged if r["topic"] == "/imu/data"]
        imu_oracle = [r for r in oracle_rows if r["topic"] == "/imu/data"]
        assert len(imu_staged) == len(imu_oracle)
