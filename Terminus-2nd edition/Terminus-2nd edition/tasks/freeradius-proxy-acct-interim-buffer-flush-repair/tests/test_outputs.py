"""Behavioral verifier for radiusproxy interim buffer flush replay."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

from reference_validator import reference_replay, reference_snapshot

APP = Path("/app")
LOGS = APP / "fixtures/radius"
CONFIG = APP / "config/radiusproxy.json"
SNAPSHOT = APP / "state/acct-flush-snapshot.json"
DB_PATH = APP / "state/acct-ledger.db"
OUTPUT = APP / "output/radius-acct-flush-report.json"
RESET = APP / "scripts/reset-state.sh"
HIDDEN = Path("/tests/fixtures-hidden/09-reboot-interim-storm.jsonl")
CLI = "/usr/local/bin/radiusproxy"

FIXTURES = [
    "01-baseline.jsonl",
    "02-interim-precedence.jsonl",
    "03-nas-reboot.jsonl",
    "04-flush-order.jsonl",
    "05-interim-storm.jsonl",
    "06-stop-pending.jsonl",
]


def _run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
    )


def reset_state() -> None:
    proc = _run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_cli() -> None:
    proc = _run(["go", "build", "-mod=vendor", "-o", CLI, "./cmd/radiusproxy"])
    assert proc.returncode == 0, proc.stderr


def ingest(logs: Path, snapshot: Path = SNAPSHOT, db: Path = DB_PATH) -> subprocess.CompletedProcess[str]:
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    return _run(
        [
            CLI,
            "ingest",
            "--logs",
            str(logs),
            "--config",
            str(CONFIG),
            "--snapshot",
            str(snapshot),
            "--db",
            str(db),
        ]
    )


def export_report(snapshot: Path = SNAPSHOT, output: Path = OUTPUT) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    return _run([CLI, "export", "--snapshot", str(snapshot), "--output", str(output)])


class TestRadiusProxyFlush:
    """End-to-end radiusproxy ingest/export against independent reference."""

    @classmethod
    def setup_class(cls) -> None:
        reset_state()
        build_cli()

    def test_public_fixtures_present(self) -> None:
        """Bundled JSONL replay logs must exist under /app/fixtures/radius/."""
        for name in FIXTURES:
            assert (LOGS / name).is_file(), name

    def test_full_replay_matches_reference(self) -> None:
        """Cumulative replay export must match independent reference replay."""
        proc = ingest(LOGS)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        pub = export_report()
        assert pub.returncode == 0, pub.stderr or pub.stdout
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_replay(LOGS, CONFIG)
        assert got == expect

    def test_staging_snapshot_written(self) -> None:
        """Ingest must write /app/state/acct-flush-snapshot.json."""
        reset_state()
        proc = ingest(LOGS)
        assert proc.returncode == 0, proc.stderr
        assert SNAPSHOT.is_file()
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        expect = reference_snapshot(LOGS, CONFIG)
        assert snap == expect

    def test_wal_checkpoint_recorded(self) -> None:
        """Ingest must record wal_checkpoints after SQLite persist."""
        reset_state()
        proc = ingest(LOGS)
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["stats"]["wal_checkpoints"] >= 1

    def test_interim_precedence_over_session_timeout(self) -> None:
        """Acct-Interim-Interval must govern flush timing when Session-Timeout is also present."""
        reset_state()
        proc = ingest(LOGS / "02-interim-precedence.jsonl")
        assert proc.returncode == 0, proc.stderr
        export_report(output=APP / "output/precedence.json")
        doc = json.loads((APP / "output/precedence.json").read_text(encoding="utf-8"))
        assert doc["stats"]["interim_flushed"] >= 1
        sess = doc["sessions"][0]
        assert sess["interim_interval_sec"] == 120

    def test_nas_reboot_separate_lineage(self) -> None:
        """NAS reboot with new Acct-Unique-Session-Id must not merge octets into prior lineage."""
        reset_state()
        proc = ingest(LOGS / "03-nas-reboot.jsonl")
        assert proc.returncode == 0, proc.stderr
        export_report(output=APP / "output/reboot.json")
        doc = json.loads((APP / "output/reboot.json").read_text(encoding="utf-8"))
        assert doc["stats"]["reboot_lineages"] >= 1
        uniq_r2 = [s for s in doc["sessions"] if s["acct_unique_session_id"] == "uniq-r2"]
        assert uniq_r2 and uniq_r2[0]["input_octets"] == 800

    def test_flush_order_by_session_start(self) -> None:
        """Flush batches must order by session_start_ts not arrival seq alone."""
        reset_state()
        proc = ingest(LOGS / "04-flush-order.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["stats"]["interim_flushed"] >= 2
        assert snap["flush_queue"] == []
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.execute(
                "SELECT seq FROM flush_ledger WHERE seq IN (32, 33) ORDER BY rowid"
            )
            seqs = [r[0] for r in cur.fetchall()]
        finally:
            conn.close()
        assert seqs == [33, 32]

    def test_export_counts_stopped_only(self) -> None:
        """sessions_completed must count stopped sessions only, not interim rows."""
        reset_state()
        ingest(LOGS / "01-baseline.jsonl")
        export_report(output=APP / "output/baseline-export.json")
        doc = json.loads((APP / "output/baseline-export.json").read_text(encoding="utf-8"))
        stopped = sum(1 for s in doc["sessions"] if s["status"] == "stopped")
        assert doc["sessions_completed"] == stopped
        assert doc["interim_flushed"] == doc["stats"]["interim_flushed"]

    def test_stop_flushes_pending_interim(self) -> None:
        """Stop must flush pending interim entries even when interval not elapsed."""
        reset_state()
        proc = ingest(LOGS / "06-stop-pending.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["stats"]["sessions_stopped"] >= 1
        assert snap["stats"]["interim_flushed"] >= 1
        assert snap["flush_queue"] == []

    def test_publish_reads_snapshot_only(self) -> None:
        """Export must not re-read JSONL logs."""
        reset_state()
        ingest(LOGS / "01-baseline.jsonl")
        before = SNAPSHOT.read_bytes()
        shutil.move(str(LOGS), str(APP / "fixtures/radius.bak"))
        try:
            pub = export_report()
            assert pub.returncode == 0, pub.stderr
            assert SNAPSHOT.read_bytes() == before
        finally:
            shutil.move(str(APP / "fixtures/radius.bak"), str(LOGS))

    def test_hidden_reboot_interim_storm(self) -> None:
        """Hidden reboot and interim storm fixture must match reference."""
        assert HIDDEN.is_file(), "missing hidden fixture"
        reset_state()
        proc = ingest(HIDDEN.parent)
        assert proc.returncode == 0, proc.stderr
        pub = export_report(output=APP / "output/hidden.json")
        assert pub.returncode == 0
        got = json.loads((APP / "output/hidden.json").read_text(encoding="utf-8"))
        expect = reference_replay(HIDDEN.parent, CONFIG)
        assert got == expect

    def test_tb3_radius_dir_override(self) -> None:
        """TB3_RADIUS_DIR absolute path must replay hidden captures."""
        tb3 = os.environ.get("TB3_RADIUS_DIR")
        if not tb3:
            pytest.skip("TB3_RADIUS_DIR not set")
        root = Path(tb3)
        if not root.is_dir():
            pytest.skip("TB3_RADIUS_DIR missing")
        reset_state()
        proc = ingest(root)
        assert proc.returncode == 0, proc.stderr
        pub = export_report(output=APP / "output/tb3.json")
        assert pub.returncode == 0
        got = json.loads((APP / "output/tb3.json").read_text(encoding="utf-8"))
        expect = reference_replay(root, CONFIG)
        assert got == expect


GOLDEN_ROOT = Path("/opt/verifier-golden-radiusproxy")
GOLDEN_MAP = {
    "interval.go": (APP / "internal/attribute/interval.go", GOLDEN_ROOT / "interval.go"),
    "dedupe.go": (APP / "internal/session/dedupe.go", GOLDEN_ROOT / "dedupe.go"),
    "queue.go": (APP / "internal/proxy/queue.go", GOLDEN_ROOT / "queue.go"),
    "sqlite.go": (APP / "internal/store/sqlite.go", GOLDEN_ROOT / "sqlite.go"),
    "stage.go": (APP / "internal/export/stage.go", GOLDEN_ROOT / "stage.go"),
    "rollup.go": (APP / "internal/export/rollup.go", GOLDEN_ROOT / "rollup.go"),
}


class TestModuleTraps:
    """Single-module golden swap must not pass full cumulative replay."""

    @classmethod
    def setup_class(cls) -> None:
        reset_state()
        build_cli()

    @pytest.mark.parametrize("name", list(GOLDEN_MAP.keys()))
    def test_single_golden_module_insufficient(self, name: str) -> None:
        """Fixing one module alone must not match reference export."""
        target, golden = GOLDEN_MAP[name]
        assert golden.is_file(), f"missing verifier golden module at {golden}"
        _run(["bash", "/app/scripts/verifier-rebuild.sh"])
        shutil.copy(golden, target)
        build_cli()
        proc = ingest(LOGS)
        pub = export_report()
        _run(["bash", "/app/scripts/verifier-rebuild.sh"])
        build_cli()
        assert proc.returncode == 0 and pub.returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_replay(LOGS, CONFIG)
        assert got != expect, f"module {name} alone must not fully fix pipeline"
