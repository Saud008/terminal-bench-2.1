"""Suppression atlas and reuse-timer forecast export tests for rdampctl."""

from __future__ import annotations

import json
import os

from bgp_refmath import reference_pipeline, reference_reuse_forecast
from rdamp_helpers import (
    FIXTURES,
    HIDDEN,
    LEDGER,
    RDAMP,
    forecast_pipeline,
    pipeline,
    read_jsonl,
    reset,
    run,
)


class TestEmitAtlas:
    def test_emit_blocked_without_run_id(self) -> None:
        """emit-atlas must fail when run_id is zero per rdampctl-cli.md."""
        reset()
        run([str(RDAMP), "compile-scenario", "--scenario", "stable-prefix", "--root", str(FIXTURES)])
        out = FIXTURES.parent / "output" / "suppression-atlas.jsonl"
        proc = run(
            [
                str(RDAMP),
                "emit-atlas",
                "--scenario",
                "stable-prefix",
                "--root",
                str(FIXTURES),
                "--out",
                str(out),
            ]
        )
        assert proc.returncode != 0

    def test_atlas_rows_match_reference_single_flap(self) -> None:
        """Atlas JSONL rows must match independent bgp_refmath suppression_lines."""
        reset()
        out = pipeline("single-flap")
        rows = read_jsonl(out)
        ref = reference_pipeline(FIXTURES, "single-flap")["rows"]
        assert rows == ref

    def test_stable_at_ms_on_decay_reuse(self) -> None:
        """stable_at_ms uses post-event withdrawn check; decay-reuse final announce leaves it null."""
        reset()
        out = pipeline("decay-reuse")
        rows = read_jsonl(out)
        ref = reference_pipeline(FIXTURES, "decay-reuse")["rows"]
        assert rows[0]["stable_at_ms"] == ref[0]["stable_at_ms"]

    def test_atlas_sorted_lex_peer_prefix(self) -> None:
        """Output lines sort by peer_id then prefix."""
        reset()
        out = pipeline("peer-split")
        rows = read_jsonl(out)
        keys = [(r["peer_id"], r["prefix"]) for r in rows]
        assert keys == sorted(keys)


class TestReuseForecast:
    def test_forecast_blocked_without_run_id(self) -> None:
        """emit-reuse-forecast must fail when run_id is zero."""
        reset()
        run([str(RDAMP), "compile-scenario", "--scenario", "stable-prefix", "--root", str(FIXTURES)])
        out = FIXTURES.parent / "output" / "rfc.jsonl"
        proc = run(
            [
                str(RDAMP),
                "emit-reuse-forecast",
                "--scenario",
                "stable-prefix",
                "--root",
                str(FIXTURES),
                "--out",
                str(out),
            ]
        )
        assert proc.returncode != 0

    def test_forecast_rows_match_reference_triple_flap(self) -> None:
        """Reuse forecast JSONL must match reference_reuse_forecast math."""
        reset()
        out = forecast_pipeline("triple-flap")
        rows = read_jsonl(out)
        ref = reference_reuse_forecast(FIXTURES, "triple-flap")
        assert rows == ref

    def test_forecast_omits_quiet_stable_prefix(self) -> None:
        """Quiet advertised routes below reuse peak must not emit forecast lines."""
        reset()
        out = forecast_pipeline("stable-prefix")
        rows = read_jsonl(out)
        assert rows == []
        assert reference_reuse_forecast(FIXTURES, "stable-prefix") == []

    def test_forecast_ms_to_reuse_closed_form(self) -> None:
        """ms_to_reuse must use exponential half-life inversion from reuse-timer-forecast.md."""
        reset()
        out = forecast_pipeline("single-flap")
        rows = read_jsonl(out)
        ref = reference_reuse_forecast(FIXTURES, "single-flap")
        assert rows[0]["ms_to_reuse"] == ref[0]["ms_to_reuse"]
        assert rows[0]["slot_digest"] == ref[0]["slot_digest"]

    def test_forecast_anchor_is_slot_last_ts(self) -> None:
        """forecast_anchor_ms must equal the slot last_ts_ms from the flap ledger."""
        reset()
        out = forecast_pipeline("decay-reuse")
        rows = read_jsonl(out)
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        key = f"{rows[0]['peer_id']}:{rows[0]['prefix']}"
        assert rows[0]["forecast_anchor_ms"] == ledger["entries"][key]["last_ts_ms"]

    def test_forecast_sorted_peer_then_prefix(self) -> None:
        """Forecast lines sort by peer_id then prefix."""
        reset()
        out = forecast_pipeline("peer-split")
        rows = read_jsonl(out)
        keys = [(r["peer_id"], r["prefix"]) for r in rows]
        assert keys == sorted(keys)


class TestHiddenTraps:
    def test_tb3_strict_reuse_hidden_fixture(self) -> None:
        """Hidden fixture under tests/vfix uses stricter reuse threshold."""
        assert HIDDEN.is_dir()
        assert any((HIDDEN / "scenarios").glob("tb3*.json"))
        reset()
        out = pipeline("tb3-sr", root=HIDDEN)
        rows = read_jsonl(out)
        ref = reference_pipeline(HIDDEN, "tb3-sr")["rows"]
        assert rows == ref

    def test_tb3_half_life_bias_env(self) -> None:
        """TB3_HALF_LIFE_BIAS shifts decay during compile-scenario on hidden peers."""
        reset()
        env = {"TB3_HALF_LIFE_BIAS": "60000", "TB3_FIXTURE_DIR": str(HIDDEN)}
        for step in (
            [str(RDAMP), "compile-scenario", "--scenario", "tb3-multi-flap", "--root", str(HIDDEN)],
            [str(RDAMP), "drive-feed", "--scenario", "tb3-multi-flap", "--root", str(HIDDEN)],
        ):
            proc = run(step, env=env)
            assert proc.returncode == 0, proc.stderr + proc.stdout
        prev_bias = os.environ.get("TB3_HALF_LIFE_BIAS")
        prev_fix = os.environ.get("TB3_FIXTURE_DIR")
        try:
            os.environ["TB3_HALF_LIFE_BIAS"] = "60000"
            os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN)
            ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
            key = "core-1:198.18.0.0/24"
            ref = reference_pipeline(HIDDEN, "tb3-multi-flap")["ledger"]["entries"][key]
            assert ledger["entries"][key]["peak_penalty"] == ref["peak_penalty"]
        finally:
            if prev_bias is None:
                os.environ.pop("TB3_HALF_LIFE_BIAS", None)
            else:
                os.environ["TB3_HALF_LIFE_BIAS"] = prev_bias
            if prev_fix is None:
                os.environ.pop("TB3_FIXTURE_DIR", None)
            else:
                os.environ["TB3_FIXTURE_DIR"] = prev_fix

    def test_tb3_multi_flap_forecast_hidden(self) -> None:
        """Hidden multi-flap scenario forecast rows match reference."""
        reset()
        out = forecast_pipeline("tb3-multi-flap", root=HIDDEN)
        rows = read_jsonl(out)
        ref = reference_reuse_forecast(HIDDEN, "tb3-multi-flap")
        assert rows == ref


class TestDecoyModule:
    def test_rib_decoy_not_required_for_cli(self) -> None:
        """Instruction states rib decoy module is off compile/replay/emit hot path."""
        decoy = FIXTURES.parent / "decoy" / "rib_decoy.rs"
        assert decoy.is_file()
        reset()
        proc = run([str(RDAMP), "compile-scenario", "--scenario", "stable-prefix", "--root", str(FIXTURES)])
        assert proc.returncode == 0
