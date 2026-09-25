"""Scenario lock compile stage tests for rdampctl — ingest UPDATE stream into staging snapshot."""

from __future__ import annotations

import json

from bgp_refmath import reference_compile_lock as compile_lock
from rdamp_helpers import (
    FIXTURES,
    LEDGER,
    LOCK,
    RDAMP,
    RUN_COUNTER,
    pipeline,
    reset,
    run,
)


class TestOutputPathContracts:
    def test_scenario_lock_path_constant(self) -> None:
        """Instruction names /app/state/scenario-lock.json as compile-scenario output."""
        assert str(LOCK) == "/app/state/scenario-lock.json"

    def test_flap_ledger_path_constant(self) -> None:
        """Instruction names /app/state/flap-ledger.json as drive-feed output."""
        assert str(LEDGER) == "/app/state/flap-ledger.json"

    def test_run_counter_path_constant(self) -> None:
        """Instruction names /app/state/run-counter.json for run_id persistence."""
        assert str(RUN_COUNTER) == "/app/state/run-counter.json"

    def test_suppression_atlas_default_path(self) -> None:
        """Instruction names /app/output/suppression-atlas.jsonl for emit-atlas."""
        reset()
        out = FIXTURES.parent / "output" / "suppression-atlas.jsonl"
        pipeline("single-flap", out_name="suppression-atlas.jsonl")
        assert out.is_file()
        assert str(out) == "/app/output/suppression-atlas.jsonl"


class TestCompileScenario:
    def test_compile_writes_scenario_lock(self) -> None:
        """Instruction requires compile-scenario to write /app/state/scenario-lock.json."""
        reset()
        proc = run([str(RDAMP), "compile-scenario", "--scenario", "stable-prefix", "--root", str(FIXTURES)])
        assert proc.returncode == 0
        assert LOCK.is_file()

    def test_lock_has_no_events_array(self) -> None:
        """Scenario lock must not embed events per scenario-lock.md."""
        reset()
        run([str(RDAMP), "compile-scenario", "--scenario", "single-flap", "--root", str(FIXTURES)])
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        assert "events" not in lock

    def test_stream_fingerprint_matches_reference(self) -> None:
        """Lock feed_fingerprint must match sha256 of raw UPDATE stream bytes."""
        reset()
        run([str(RDAMP), "compile-scenario", "--scenario", "single-flap", "--root", str(FIXTURES)])
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        ref = compile_lock(FIXTURES, "single-flap")
        assert lock["feed_fingerprint"] == ref["feed_fingerprint"]

    def test_peer_table_keeps_peer_reuse_threshold(self) -> None:
        """Peer dampening table must preserve per-peer reuse_threshold."""
        reset()
        run([str(RDAMP), "compile-scenario", "--scenario", "peer-split", "--root", str(FIXTURES)])
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        assert lock["peer_table"]["edge-b"]["reuse_threshold"] == 600
