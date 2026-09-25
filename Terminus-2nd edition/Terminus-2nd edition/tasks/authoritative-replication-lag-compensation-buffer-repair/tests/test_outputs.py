"""Verifier for authoritative-replication-lag-compensation-buffer-repair."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from reference_lag import ewma_lag_us, merge_snapshot_rows, merged_state_hash

APP = Path("/app")
INGEST_TRACE = APP / "fixtures" / "traces" / "baseline_ingest.jsonl"
BASE_INGEST = INGEST_TRACE
SIM_TRACE = APP / "fixtures" / "traces" / "baseline_sim.jsonl"
HIDDEN_INGEST = Path("/opt/verifier-fixtures/replic-lag/packet_loss/ingest.jsonl")
DB = APP / "data" / "replic.db"
MANIFEST = APP / "state" / "ingest-manifest.json"
REPORT = APP / "state" / "sim-report.json"
BUNDLE = APP / "output" / "snapshot-bundle.json"
AUDIT = APP / "state" / "export-audit.json"
ROLLBACK_MIN = 30
INTEGRITY_SEED = 0xA5A5A5A5


def reset() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def ingest(trace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "replag-sim",
            "ingest",
            "--trace",
            str(trace),
            "--db",
            str(DB),
            "--manifest",
            str(MANIFEST),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def export() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "replag-sim",
            "export-snapshot",
            "--db",
            str(DB),
            "--bundle",
            str(BUNDLE),
            "--audit",
            str(AUDIT),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def simulate() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "replag-sim",
            "simulate",
            "--trace",
            str(SIM_TRACE),
            "--db",
            str(DB),
            "--report",
            str(REPORT),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(autouse=True)
def _clean() -> None:
    reset()


class TestLagBufferIngest:
    """Lag estimate, compensation buffer, ingest, ledger, and reconnect."""

    def test_ingest_manifest_read_head_after_late_reject(self) -> None:
        """Ingest must leave read_head at 5 when late frame 2 is rejected against head 5."""
        proc = run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                str(INGEST_TRACE),
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert doc["read_head"] == 5
        assert doc["events_total"] == 5

    def test_ewma_lag_estimate_not_mean(self) -> None:
        """Sim report lag must match EWMA reference, not arithmetic mean of RTT samples."""
        run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                str(INGEST_TRACE),
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ]
        )
        proc = run(
            [
                "replag-sim",
                "simulate",
                "--trace",
                str(SIM_TRACE),
                "--db",
                str(DB),
                "--report",
                str(REPORT),
                "--tick-rate",
                "60",
            ]
        )
        assert proc.returncode == 0, proc.stderr
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        expected = ewma_lag_us([40000, 50000, 44000])
        assert report["lag_method"] == "ewma"
        assert report["lag_estimate_us"] == expected
        assert report["lag_estimate_us"] != sum([40000, 50000, 44000]) // 3

    def test_buffer_applies_only_after_ack(self) -> None:
        """Only the acknowledged input may count toward buffered_inputs_applied."""
        run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                str(INGEST_TRACE),
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ]
        )
        run(
            [
                "replag-sim",
                "simulate",
                "--trace",
                str(SIM_TRACE),
                "--db",
                str(DB),
                "--report",
                str(REPORT),
            ]
        )
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report["buffered_inputs_applied"] == 1

    def test_duplicate_input_skipped_in_ledger(self) -> None:
        """Duplicate input_seq must increment duplicate_inputs_skipped."""
        run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                str(INGEST_TRACE),
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ]
        )
        run(
            [
                "replag-sim",
                "simulate",
                "--trace",
                str(SIM_TRACE),
                "--db",
                str(DB),
                "--report",
                str(REPORT),
            ]
        )
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report["duplicate_inputs_skipped"] == 1

    def test_late_frame_rejected_without_shrinking_read_head(self) -> None:
        """Late frame 3 must be rejected while read_head stays 5 from ingest."""
        run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                str(INGEST_TRACE),
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ]
        )
        run(
            [
                "replag-sim",
                "simulate",
                "--trace",
                str(SIM_TRACE),
                "--db",
                str(DB),
                "--report",
                str(REPORT),
            ]
        )
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report["late_frames_rejected"] == 1
        assert report["read_head"] == 5

    def test_reconnect_does_not_shrink_rollback_window(self) -> None:
        """Reconnect rollback_ticks 10 must keep rollback_window_ticks at max(prior, 30, 10)."""
        run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                str(INGEST_TRACE),
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ]
        )
        run(
            [
                "replag-sim",
                "simulate",
                "--trace",
                str(SIM_TRACE),
                "--db",
                str(DB),
                "--report",
                str(REPORT),
            ]
        )
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        prior_window = ROLLBACK_MIN
        reconnect_ticks = 10
        expected = max(prior_window, ROLLBACK_MIN, reconnect_ticks)
        assert report["rollback_window_ticks"] == expected

    def test_tb3_tick_rate_env_override(self) -> None:
        """TB3_TICK_RATE_HZ must apply when simulate --tick-rate is zero."""
        run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                str(INGEST_TRACE),
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ]
        )
        env = os.environ.copy()
        env["TB3_TICK_RATE_HZ"] = "120"
        proc = subprocess.run(
            [
                "replag-sim",
                "simulate",
                "--trace",
                str(SIM_TRACE),
                "--db",
                str(DB),
                "--report",
                str(REPORT),
                "--tick-rate",
                "0",
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report["tick_rate_hz"] == 120

    def test_tb3_trace_dir_override_for_simulate(self) -> None:
        """TB3_TRACE_DIR must resolve a basename trace like the full fixtures path."""
        trace_dir = APP / "fixtures" / "traces"
        run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                str(INGEST_TRACE),
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ]
        )
        env = os.environ.copy()
        env["TB3_TRACE_DIR"] = str(trace_dir)
        proc = subprocess.run(
            [
                "replag-sim",
                "simulate",
                "--trace",
                "baseline_sim.jsonl",
                "--db",
                str(DB),
                "--report",
                str(REPORT),
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert REPORT.is_file()


class TestSnapshotExport:
    """Snapshot merge ordering, gap fill, and integrity export."""

    def test_baseline_bundle_gap_fill_and_merge_order(self) -> None:
        """Bundled ingest trace must export gap-filled cumulative XOR rows."""
        assert ingest(BASE_INGEST).returncode == 0
        assert export().returncode == 0
        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        deltas = [(1, 0, 10), (2, 1, 20), (4, 3, 40)]
        expected_rows = merge_snapshot_rows(deltas)
        assert bundle["gap_fills"] == 1
        assert len(bundle["snapshots"]) == len(expected_rows)
        for got, (seq, hash_val) in zip(bundle["snapshots"], expected_rows, strict=True):
            assert got["seq"] == seq
            assert got["state_hash"] == hash_val

    def test_baseline_integrity_chain_matches_seed_xor_merged(self) -> None:
        """integrity_chain must equal integrity_seed XOR merged_state_hash."""
        assert ingest(BASE_INGEST).returncode == 0
        assert export().returncode == 0
        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        merged = merged_state_hash([(1, 0, 10), (2, 1, 20), (4, 3, 40)])
        chain = INTEGRITY_SEED ^ merged
        assert bundle["merged_state_hash"] == merged
        assert bundle["integrity_chain"] == chain
        assert audit["merged_state_hash"] == merged
        assert audit["integrity_chain"] == chain
        assert audit["snapshot_count"] == 4

    def test_hidden_packet_loss_trace_read_head(self) -> None:
        """Hidden ingest with loss must keep read_head 14 after rejecting late frame 11."""
        assert HIDDEN_INGEST.is_file(), "hidden packet loss fixtures missing"
        proc = ingest(HIDDEN_INGEST)
        assert proc.returncode == 0, proc.stderr
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["read_head"] == 14

    def test_hidden_packet_loss_export_matches_reference(self) -> None:
        """Hidden trace export must match independent gap-fill merge reference."""
        assert ingest(HIDDEN_INGEST).returncode == 0
        assert export().returncode == 0
        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        deltas = [(10, 9, 7), (12, 11, 9), (13, 12, 3)]
        expected_rows = merge_snapshot_rows(deltas)
        merged = merged_state_hash(deltas)
        assert bundle["gap_fills"] == 1
        assert bundle["merged_state_hash"] == merged
        for got, (seq, hash_val) in zip(bundle["snapshots"], expected_rows, strict=True):
            assert got["seq"] == seq
            assert got["state_hash"] == hash_val

    def test_export_without_ingest_fails(self) -> None:
        """Export without ingest must fail because no snapshot deltas exist."""
        reset()
        proc = export()
        assert proc.returncode != 0

    def test_tb3_trace_dir_override_for_ingest(self) -> None:
        """TB3_TRACE_DIR must resolve a basename ingest trace like the fixtures path."""
        trace_dir = APP / "fixtures" / "traces"
        env = os.environ.copy()
        env["TB3_TRACE_DIR"] = str(trace_dir)
        proc = subprocess.run(
            [
                "replag-sim",
                "ingest",
                "--trace",
                "baseline_ingest.jsonl",
                "--db",
                str(DB),
                "--manifest",
                str(MANIFEST),
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["read_head"] == 5

    def test_sim_ewma_and_buffer_still_correct(self) -> None:
        """Simulate must still report EWMA lag and ack-buffered inputs alongside export."""
        assert ingest(BASE_INGEST).returncode == 0
        proc = simulate()
        assert proc.returncode == 0, proc.stderr + proc.stdout
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        expected = ewma_lag_us([40000, 50000, 44000])
        assert report["lag_method"] == "ewma"
        assert report["lag_estimate_us"] == expected
        assert report["buffered_inputs_applied"] == 1

    def test_ingest_read_head_still_correct(self) -> None:
        """Ingest read_head contract must remain valid alongside export."""
        assert ingest(BASE_INGEST).returncode == 0
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["read_head"] == 5

    def test_export_audit_snapshot_count_matches_bundle(self) -> None:
        """export-audit.json snapshot_count must match snapshot-bundle.json length."""
        assert ingest(BASE_INGEST).returncode == 0
        assert export().returncode == 0
        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        assert bundle["gap_fills"] == 1
        assert audit["snapshot_count"] == len(bundle["snapshots"])
        assert audit["merged_state_hash"] == bundle["merged_state_hash"]

    def test_hidden_packet_loss_integrity_chain(self) -> None:
        """Hidden packet-loss export integrity_chain must equal seed XOR merged hash."""
        assert ingest(HIDDEN_INGEST).returncode == 0
        assert export().returncode == 0
        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        deltas = [(10, 9, 7), (12, 11, 9), (13, 12, 3)]
        merged = merged_state_hash(deltas)
        chain = INTEGRITY_SEED ^ merged
        assert bundle["integrity_chain"] == chain
        assert audit["integrity_chain"] == chain
