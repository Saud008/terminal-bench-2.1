"""Replay-feed dampening ledger tests via /app/bin/rdampctl subprocess."""

from __future__ import annotations

import json

from bgp_refmath import apply_decay, reference_pipeline
from rdamp_helpers import FIXTURES, LEDGER, RDAMP, RUN_COUNTER, pipeline, reset, run


class TestDriveFeed:
    def test_replay_bumps_run_counter(self) -> None:
        """Instruction requires drive-feed to increment run_id in /app/state/run-counter.json."""
        reset()
        pipeline("stable-prefix")
        run_id = json.loads(RUN_COUNTER.read_text(encoding="utf-8"))["run_id"]
        assert run_id >= 1

    def test_exponential_decay_half_life(self) -> None:
        """Half-life decay must use exponential factor from half-life-decay.md."""
        assert apply_decay(1000, 0, 300_000, 300_000) == 500
        assert apply_decay(1000, 0, 600_000, 300_000) == 250

    def test_single_flap_penalty_and_count(self) -> None:
        """Withdraw after established route accrues flap_penalty once."""
        reset()
        pipeline("single-flap")
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        key = "edge-a:192.168.10.0/24"
        ref = reference_pipeline(FIXTURES, "single-flap")["ledger"]["entries"][key]
        got = ledger["entries"][key]
        assert got["flap_count"] == ref["flap_count"] == 1
        assert got["penalty"] == ref["penalty"]

    def test_triple_flap_suppression(self) -> None:
        """Repeated flaps must reach suppress_threshold and set suppressed true."""
        reset()
        pipeline("triple-flap")
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        key = "edge-a:172.16.1.0/24"
        ref = reference_pipeline(FIXTURES, "triple-flap")["ledger"]["entries"][key]
        got = ledger["entries"][key]
        assert got["suppressed"] is True
        assert got["flap_count"] == ref["flap_count"] == 3

    def test_attribute_refresh_no_flap(self) -> None:
        """Second announce while advertised must not increment flap_count."""
        reset()
        pipeline("stable-prefix")
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        got = ledger["entries"]["edge-a:10.1.0.0/24"]
        assert got["flap_count"] == 0
        assert got["advertised"] is True

    def test_decay_reuse_final_penalty(self) -> None:
        """Long idle gap must decay penalty before re-announce."""
        reset()
        pipeline("decay-reuse")
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        key = "edge-a:10.20.0.0/24"
        ref = reference_pipeline(FIXTURES, "decay-reuse")["ledger"]["entries"][key]
        assert ledger["entries"][key]["penalty"] == ref["penalty"]

    def test_peer_split_independent_state(self) -> None:
        """Each peer ledger entry must use that peer dampening table row."""
        reset()
        pipeline("peer-split")
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        ref = reference_pipeline(FIXTURES, "peer-split")["ledger"]["entries"]
        for peer in ("edge-a", "edge-b"):
            key = f"{peer}:203.0.113.0/24"
            assert ledger["entries"][key]["penalty"] == ref[key]["penalty"]

    def test_replay_sorts_numeric_ts(self) -> None:
        """Replay must order UPDATE stream by numeric ts_ms when re-reading from disk."""
        reset()
        run([str(RDAMP), "compile-scenario", "--scenario", "peer-split", "--root", str(FIXTURES)])
        run([str(RDAMP), "drive-feed", "--scenario", "peer-split", "--root", str(FIXTURES)])
        ref = reference_pipeline(FIXTURES, "peer-split")["ledger"]["entries"]
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        assert ledger["entries"]["edge-a:203.0.113.0/24"]["flap_count"] == ref["edge-a:203.0.113.0/24"]["flap_count"]
