"""Behavioral verifier for wantplay swarm-trade wantlist arena playtest."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from bitswap_trace_math import (
    load_trace_events,
    reference_bitswap_metrics,
    reference_bitswap_session,
)

APP = Path("/app")
CLI = "/usr/local/bin/wantplay"
FIXTURES = APP / "fixtures/exchange"
DEFAULT_HIDDEN = Path("/tests/hidden/exchange")
STAGING = Path("/app/state/want-snapshot.json")
OUT = Path("/app/output")
SESSION_REPORT = "/app/output/session-report.json"
METRICS_REPORT = "/app/output/metrics-report.json"
RESET = APP / "scripts/reset-state.sh"
SEED = os.environ.get("VERIFIER_SEED", "bitswap-wantlist-session-seal-ledger")
SESSION_PREFIX = os.environ.get("TB3_SESSION_PREFIX", "tb3")

METRICS_FIXTURE = "006-priority-cancel.jsonl"


def hidden_fixtures_dir() -> Path:
    """Resolve held-out fixture directory; TB3_FIXTURES_DIR overrides the default path."""
    override = os.environ.get("TB3_FIXTURES_DIR", "").strip()
    if override:
        return Path(override)
    return DEFAULT_HIDDEN


def session_name(suffix: str) -> str:
    digest = hashlib.sha256(f"{SEED}:{suffix}".encode()).hexdigest()[:8]
    return f"{SESSION_PREFIX}-{digest}"


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pipeline(fixture: Path, suffix: str) -> subprocess.CompletedProcess[str]:
    sess = session_name(suffix)
    out = OUT / f"export-{suffix}.json"
    return run(
        [
            CLI,
            "pipeline",
            "--log",
            str(fixture),
            "--session",
            sess,
            "--output",
            str(out),
        ]
    )


def metrics(fixture: Path, suffix: str) -> subprocess.CompletedProcess[str]:
    sess = session_name(suffix)
    out = OUT / f"metrics-{suffix}.json"
    return run(
        [
            CLI,
            "metrics",
            "--log",
            str(fixture),
            "--session",
            sess,
            "--output",
            str(out),
        ]
    )


class TestBitswapPipeline:
    def _assert_export_matches_reference(self, fixture_file: str) -> None:
        reset()
        fixture = FIXTURES / fixture_file
        suffix = fixture_file.replace(".jsonl", "")
        proc = pipeline(fixture, suffix)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        out = OUT / f"export-{suffix}.json"
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref_snap = reference_bitswap_session(load_trace_events(fixture), session_name(suffix))
        assert cli["session_id"] == ref_snap["session_id"]
        assert cli["wants_remaining"] == ref_snap["wants_remaining"]
        assert cli["delivered"] == ref_snap["delivered"]
        assert cli["ledger_totals"] == ref_snap["ledger_totals"]
        assert cli["partial_blocks"] == ref_snap["partial_blocks"]
        assert cli["in_flight_count"] == ref_snap["in_flight_count"]
        assert cli["delivery_count"] == len(ref_snap["delivered"])

    def test_t7ed40b_export_basic_wants(self) -> None:
        """Bundled 001-basic-wants export matches reference_bitswap_session."""
        self._assert_export_matches_reference("001-basic-wants.jsonl")

    def test_t7ed40b_export_alias_merge(self) -> None:
        """Bundled 002-alias-merge export matches reference_bitswap_session."""
        self._assert_export_matches_reference("002-alias-merge.jsonl")

    def test_t7ed40b_export_cancel_inflight(self) -> None:
        """Bundled 003-cancel-inflight export matches reference_bitswap_session."""
        self._assert_export_matches_reference("003-cancel-inflight.jsonl")

    def test_t7ed40b_export_ledger_dedupe(self) -> None:
        """Bundled 004-ledger-dedupe export matches reference_bitswap_session."""
        self._assert_export_matches_reference("004-ledger-dedupe.jsonl")

    def test_t7ed40b_export_idle_partial(self) -> None:
        """Bundled 005-idle-partial export matches reference_bitswap_session."""
        self._assert_export_matches_reference("005-idle-partial.jsonl")

    def test_t7ed40b_export_pipeline_mixed(self) -> None:
        """Bundled 007-pipeline-mixed export matches reference_bitswap_session."""
        self._assert_export_matches_reference("007-pipeline-mixed.jsonl")

    def test_t7ed40b_delivered_rows_use_display_cid(self) -> None:
        """Delivered rows keep display CID strings from want entries after alias merge."""
        reset()
        fixture = FIXTURES / "002-alias-merge.jsonl"
        proc = pipeline(fixture, "display-cid")
        assert proc.returncode == 0, proc.stderr
        export = json.loads((OUT / "export-display-cid.json").read_text(encoding="utf-8"))
        ref = reference_bitswap_session(load_trace_events(fixture), session_name("display-cid"))
        assert export["delivered"] == ref["delivered"]
        for row in export["delivered"]:
            assert not row["cid"].startswith("a1")

    def test_t7ed40b_ledger_totals_display_cid(self) -> None:
        """Ledger totals credit display CID once per peer even with duplicate block_done."""
        reset()
        fixture = FIXTURES / "004-ledger-dedupe.jsonl"
        proc = pipeline(fixture, "ledger-display")
        assert proc.returncode == 0, proc.stderr
        export = json.loads((OUT / "export-ledger-display.json").read_text(encoding="utf-8"))
        ref = reference_bitswap_session(load_trace_events(fixture), session_name("ledger-display"))
        assert export["ledger_totals"] == ref["ledger_totals"]
        for row in export["ledger_totals"]:
            assert row["cid"].startswith("bafy") or row["cid"].startswith("Qm")

    def test_t7ed40b_staging_snapshot_matches_reference(self) -> None:
        """Staging snapshot at /app/state/want-snapshot.json matches reference ingest."""
        reset()
        fixture = FIXTURES / "007-pipeline-mixed.jsonl"
        proc = pipeline(fixture, "staging-check")
        assert proc.returncode == 0, proc.stderr
        assert STAGING.is_file(), "want-snapshot.json missing"
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        ref = reference_bitswap_session(load_trace_events(fixture), session_name("staging-check"))
        assert snap["wants_remaining"] == ref["wants_remaining"]
        assert snap["delivered"] == ref["delivered"]
        assert snap["ledger_totals"] == ref["ledger_totals"]
        assert snap["partial_blocks"] == ref["partial_blocks"]
        assert snap["in_flight_count"] == ref["in_flight_count"]

    def test_t7ed40b_export_reads_snapshot_not_scratch(self) -> None:
        """Export wants_remaining must match staging snapshot, not scratch manifest keys."""
        reset()
        fixture = FIXTURES / "002-alias-merge.jsonl"
        proc = pipeline(fixture, "scratch-probe")
        assert proc.returncode == 0, proc.stderr
        export = json.loads((OUT / "export-scratch-probe.json").read_text(encoding="utf-8"))
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert export["wants_remaining"] == snap["wants_remaining"]

    def test_t7ed40b_metrics_queue_head(self) -> None:
        """Metrics report queue head matches reference priority scheduling."""
        reset()
        fixture = FIXTURES / METRICS_FIXTURE
        proc = metrics(fixture, "metrics-head")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        cli = json.loads((OUT / "metrics-metrics-head.json").read_text(encoding="utf-8"))
        ref = reference_bitswap_metrics(load_trace_events(fixture), session_name("metrics-head"))
        assert cli == ref


class TestHiddenBitswapTraps:
    def test_t7ed40b_agent_image_has_no_hidden_fixtures(self) -> None:
        """Agent runtime image must not bake held-out verifier traces under /opt/verifier-fixtures."""
        opt_hidden = Path("/opt/verifier-fixtures/exchange")
        if opt_hidden.exists():
            leaked = list(opt_hidden.glob("*.jsonl"))
            assert leaked == [], f"held-out fixtures visible to agents: {leaked}"

    def test_t7ed40b_session_id_honors_dynamic_name(self) -> None:
        """Pipeline session_id must equal the dynamic TB3_SESSION_PREFIX hash name."""
        reset()
        fixture = FIXTURES / "001-basic-wants.jsonl"
        suffix = "dyn-session"
        sess = session_name(suffix)
        assert sess.startswith(SESSION_PREFIX)
        out = OUT / f"export-{suffix}.json"
        proc = run(
            [
                CLI,
                "pipeline",
                "--log",
                str(fixture),
                "--session",
                sess,
                "--output",
                str(out),
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        export = json.loads(out.read_text(encoding="utf-8"))
        assert export["session_id"] == sess

    def test_t7ed40b_hidden_alias_dedupe(self) -> None:
        """Held-out TB3_FIXTURES_DIR alias merge collapses to one want with max priority."""
        reset()
        fixture = hidden_fixtures_dir() / "hidden-alias-dedupe.jsonl"
        assert fixture.is_file(), f"missing held-out fixture under TB3_FIXTURES_DIR path {fixture}"
        proc = pipeline(fixture, "hidden-alias")
        assert proc.returncode == 0, proc.stderr
        export = json.loads((OUT / "export-hidden-alias.json").read_text(encoding="utf-8"))
        ref = reference_bitswap_session(load_trace_events(fixture), session_name("hidden-alias"))
        assert export["wants_remaining"] == ref["wants_remaining"]
        assert export["delivered"] == ref["delivered"]

    def test_t7ed40b_hidden_cancel_inflight_delivery(self) -> None:
        """Held-out TB3_FIXTURES_DIR cancel during in-flight still records delivery at original priority."""
        reset()
        fixture = hidden_fixtures_dir() / "hidden-cancel-inflight.jsonl"
        assert fixture.is_file(), f"missing held-out fixture under TB3_FIXTURES_DIR path {fixture}"
        proc = pipeline(fixture, "hidden-inflight")
        assert proc.returncode == 0, proc.stderr
        export = json.loads((OUT / "export-hidden-inflight.json").read_text(encoding="utf-8"))
        ref = reference_bitswap_session(load_trace_events(fixture), session_name("hidden-inflight"))
        assert export["in_flight_count"] == ref["in_flight_count"]
        assert export["delivered"] == ref["delivered"]
        assert export["delivered"][0]["priority"] == ref["delivered"][0]["priority"]

    def test_t7ed40b_hidden_ledger_credit_once(self) -> None:
        """Held-out TB3_FIXTURES_DIR duplicate block_done must not double ledger credit."""
        reset()
        fixture = hidden_fixtures_dir() / "hidden-ledger-once.jsonl"
        assert fixture.is_file(), f"missing held-out fixture under TB3_FIXTURES_DIR path {fixture}"
        proc = pipeline(fixture, "hidden-ledger")
        assert proc.returncode == 0, proc.stderr
        export = json.loads((OUT / "export-hidden-ledger.json").read_text(encoding="utf-8"))
        ref = reference_bitswap_session(load_trace_events(fixture), session_name("hidden-ledger"))
        assert export["ledger_totals"] == ref["ledger_totals"]

    def test_t7ed40b_hidden_idle_partial_flush(self) -> None:
        """Held-out TB3_FIXTURES_DIR idle tick clears partial buffers and matching wants_remaining."""
        reset()
        fixture = hidden_fixtures_dir() / "hidden-idle-flush.jsonl"
        assert fixture.is_file(), f"missing held-out fixture under TB3_FIXTURES_DIR path {fixture}"
        proc = pipeline(fixture, "hidden-idle")
        assert proc.returncode == 0, proc.stderr
        export = json.loads((OUT / "export-hidden-idle.json").read_text(encoding="utf-8"))
        ref = reference_bitswap_session(load_trace_events(fixture), session_name("hidden-idle"))
        assert export["partial_blocks"] == ref["partial_blocks"]
        assert export["wants_remaining"] == ref["wants_remaining"]
        assert export["partial_blocks"] == 0
        assert export["wants_remaining"] == []

    def test_t7ed40b_hidden_priority_head(self) -> None:
        """Held-out TB3_FIXTURES_DIR metrics trap requires tombstoned cancel blocks resurrection."""
        reset()
        fixture = hidden_fixtures_dir() / "hidden-priority-head.jsonl"
        assert fixture.is_file(), f"missing held-out fixture under TB3_FIXTURES_DIR path {fixture}"
        proc = metrics(fixture, "hidden-priority")
        assert proc.returncode == 0, proc.stderr
        cli = json.loads((OUT / "metrics-hidden-priority.json").read_text(encoding="utf-8"))
        ref = reference_bitswap_metrics(load_trace_events(fixture), session_name("hidden-priority"))
        assert cli["queue_head_cid"] == ref["queue_head_cid"]
        assert cli["queue_head_priority"] == ref["queue_head_priority"]
