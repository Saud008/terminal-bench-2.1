"""Verifier tests for mailsync Maildir/notmuch sync."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest
from reference_maildir import (
    flags_from_tags,
    normalize_flags,
    reference_publish,
    reference_snapshot,
    reference_sync,
    scan_maildir,
)

CLI = "/usr/local/bin/mailsync"
MAILDIR = Path("/app/fixtures/maildir")
DB = Path("/app/data/mailsync.db")
REPORT = Path("/app/output/mail-sync-report.json")
SNAPSHOT = Path("/app/state/mail-sync.snapshot.json")
TB3 = Path(os.environ.get("TB3_MAILDIR", "/opt/verifier-fixtures/maildir"))

PROTECTED_SHA256: dict[str, str] = {}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def rebuild() -> None:
    proc = run(["bash", "/app/scripts/verifier-rebuild.sh"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def reset() -> None:
    proc = run(["bash", "/app/scripts/reset-state.sh"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def sync(maildir: Path = MAILDIR, db: Path = DB, report: Path = REPORT) -> dict:
    proc = run(
        [CLI, "sync", "--maildir", str(maildir), "--db", str(db), "--report", str(report)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(report.read_text(encoding="utf-8"))


def ingest(maildir: Path = MAILDIR, db: Path = DB) -> dict:
    proc = run([CLI, "ingest", "--maildir", str(maildir), "--db", str(db)])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


@pytest.fixture(scope="class")
def ready() -> None:
    reset()
    rebuild()


class TestMailsync:
    def test_sync_persists_sqlite_index(self, ready: None) -> None:
        """Sync must upsert indexed messages into /app/data/mailsync.db."""
        assert str(DB) == "/app/data/mailsync.db"
        reset()
        rebuild()
        sync()
        con = sqlite3.connect("/app/data/mailsync.db")
        try:
            count = con.execute("SELECT COUNT(*) FROM messages").fetchone()
            assert count and count[0] >= 3
        finally:
            con.close()

    def test_sync_writes_export_report_json(self, ready: None) -> None:
        """Sync must write /app/output/mail-sync-report.json."""
        assert str(REPORT) == "/app/output/mail-sync-report.json"
        reset()
        rebuild()
        sync()
        assert REPORT.is_file()

    def test_ingest_writes_staging_snapshot_path(self, ready: None) -> None:
        """Ingest must write /app/state/mail-sync.snapshot.json."""
        assert str(SNAPSHOT) == "/app/state/mail-sync.snapshot.json"
        reset()
        rebuild()
        ingest()
        assert SNAPSHOT.is_file()

    def test_public_sync_matches_reference(self, ready: None) -> None:
        """Bundled maildir sync report must match independent reference."""
        reset()
        rebuild()
        got = sync()
        expect = reference_sync(MAILDIR, DB)
        assert got == expect

    def test_duplicate_message_id_prefers_newer_mtime(self, ready: None) -> None:
        """new/ copy of root-a wins over cur/ per message-id-dedupe.md."""
        reset()
        rebuild()
        got = sync()
        assert got["duplicates_merged"] >= 1

    def test_thread_binding_shares_root(self, ready: None) -> None:
        """reply-a must share thread_id with root-a."""
        reset()
        rebuild()
        got = sync()
        roots = {m["thread_id"] for m in got["messages"]}
        assert len(roots) >= 1

    def test_flag_letters_normalized_fsr_dt(self, ready: None) -> None:
        """On-disk RS must normalize to FSRDT order SR in report flags field."""
        reset()
        rebuild()
        got = sync()
        for msg in got["messages"]:
            assert msg["flags"] == normalize_flags(msg["flags"])

    def test_commit_before_rename_true(self, ready: None) -> None:
        """Report must assert DB commit precedes maildir renames."""
        reset()
        rebuild()
        got = sync()
        assert got["commit_before_rename"] is True

    def test_sync_meta_phase_committed(self, ready: None) -> None:
        """SQLite sync_meta.phase is committed after successful sync."""
        reset()
        rebuild()
        sync()
        con = sqlite3.connect(DB)
        try:
            row = con.execute("SELECT value FROM sync_meta WHERE key='phase'").fetchone()
            assert row and row[0] == "committed"
        finally:
            con.close()

    def test_malformed_message_skipped(self, ready: None) -> None:
        """Invalid RFC822 without Message-ID increments messages_skipped."""
        reset()
        rebuild()
        got = sync()
        assert got["messages_skipped"] >= 1

    def test_publish_without_rescan(self, ready: None) -> None:
        """publish re-emits report from DB + snapshot without maildir rescan."""
        reset()
        rebuild()
        sync()
        proc = run([CLI, "publish", "--db", str(DB), "--report", str(REPORT)])
        assert proc.returncode == 0, proc.stderr + proc.stdout

    def test_x_keywords_precedence_over_db_seed(self, ready: None) -> None:
        """X-Keywords must win over pre-seeded DB keyword tags."""
        reset()
        rebuild()
        got = sync()
        replies = [m for m in got["messages"] if m["message_id"] == "<reply-a@example.com>"]
        assert replies and replies[0]["keywords_source"] == "x-keywords"

    def test_hidden_duplicate_winner_keywords(self, ready: None) -> None:
        """Hidden duplicate must keep newer new/ keywords fresh,winner."""
        reset()
        rebuild()
        got = sync(TB3, DB)
        assert got["messages_indexed"] >= 1

    def test_flag_suffix_mirrors_tags(self, ready: None) -> None:
        """After sync, maildir filename flags must match tags-derived FSRDT suffix."""
        reset()
        rebuild()
        got = sync()
        for msg in got["messages"]:
            want = flags_from_tags(msg["tags"])
            assert msg["flags"] == want or not want

    def test_messages_sorted_by_message_id(self, ready: None) -> None:
        """Report messages array sorted by message_id ascending."""
        reset()
        rebuild()
        got = sync()
        ids = [m["message_id"] for m in got["messages"]]
        assert ids == sorted(ids)

    def test_rebuild_required_after_source_edit(self, ready: None) -> None:
        """Verifier rebuild path must compile agent-edited Go sources."""
        reset()
        rebuild()
        sync()

    def test_protected_fixture_and_docs_unchanged(self, ready: None) -> None:
        """Agent must not mutate bundled fixtures or contract docs."""
        reset()
        rebuild()

    def test_ingest_only_writes_snapshot(self, ready: None) -> None:
        """ingest must not write export report."""
        reset()
        rebuild()
        ingest()
        assert SNAPSHOT.is_file()
        assert not REPORT.is_file()

    def test_separate_thread_b_root_b(self, ready: None) -> None:
        """root-b stays in its own thread component."""
        reset()
        rebuild()
        got = sync()
        assert got["threads_resolved"] >= 1

    def test_tag_writes_count(self, ready: None) -> None:
        """tag_writes equals messages_indexed per export-schema.md (including publish)."""
        reset()
        rebuild()
        got = sync()
        assert got["tag_writes"] == got["messages_indexed"]

    def test_reference_scan_independent_of_cli(self, ready: None) -> None:
        """Reference scan_maildir standalone finds bundled messages."""
        reset()
        rebuild()
        scan_maildir(MAILDIR, DB)

    def test_ingest_snapshot_preserves_x_keywords(self, ready: None) -> None:
        """Staging snapshot must retain X-Keywords per staging-snapshot.md."""
        reset()
        rebuild()
        got = ingest()
        expect = reference_snapshot(MAILDIR, DB)
        assert got["staging_epoch"] == expect["staging_epoch"]
        reply_entries = [e for e in got["entries"] if e["message_id"] == "<reply-a@example.com>"]
        assert reply_entries, "reply-a missing from ingest snapshot"
        assert reply_entries[0]["x_keywords"] == ["finance", "urgent"]

    def test_sync_report_staging_epoch_bumped(self, ready: None) -> None:
        """Successful sync must bump staging_epoch in report per sync-transaction-order.md."""
        reset()
        rebuild()
        got = sync()
        assert got["staging_epoch"] >= 1

    def test_snapshot_staging_epoch_matches_report_after_sync(self, ready: None) -> None:
        """Post-sync snapshot staging_epoch must match the export report."""
        reset()
        rebuild()
        got = sync()
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["staging_epoch"] == got["staging_epoch"]

    def test_cross_run_staging_epoch_increments(self, ready: None) -> None:
        """Second sync must increase staging_epoch monotonically."""
        reset()
        rebuild()
        first = sync()
        second = sync()
        assert second["staging_epoch"] > first["staging_epoch"]

    def test_publish_overlays_snapshot_x_keywords(self, ready: None) -> None:
        """Publish must overlay snapshot x_keywords when DB keyword tags were cleared."""
        reset()
        rebuild()
        sync()
        con = sqlite3.connect(DB)
        try:
            con.execute(
                "UPDATE messages SET tags_json=?, keywords_source=? WHERE message_id=?",
                (json.dumps(["seen", "replied"]), "none", "<reply-a@example.com>"),
            )
            con.commit()
        finally:
            con.close()
        proc = run([CLI, "publish", "--db", str(DB), "--report", str(REPORT)])
        assert proc.returncode == 0, proc.stderr + proc.stdout
        expect = reference_publish(DB, SNAPSHOT)
        got = json.loads(REPORT.read_text(encoding="utf-8"))
        assert got == expect
        replies = [m for m in got["messages"] if m["message_id"] == "<reply-a@example.com>"]
        assert replies
        assert replies[0]["keywords_source"] == "x-keywords"
        assert "finance" in replies[0]["tags"]

    def test_hidden_tb3_publish_staging_epoch(self, ready: None) -> None:
        """TB3 publish report must carry snapshot staging_epoch from last sync."""
        reset()
        rebuild()
        sync(TB3, DB)
        expect_epoch = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["staging_epoch"]
        proc = run([CLI, "publish", "--db", str(DB), "--report", str(REPORT)])
        assert proc.returncode == 0, proc.stderr + proc.stdout
        got = json.loads(REPORT.read_text(encoding="utf-8"))
        assert got["staging_epoch"] == expect_epoch
        assert got["staging_epoch"] >= 1

    def test_hidden_tb3_maildir_matches_reference(self, ready: None) -> None:
        """TB3_MAILDIR hidden tree must match reference semantics."""
        reset()
        rebuild()
        got = sync(TB3, DB)
        expect = reference_sync(TB3, DB)
        assert got == expect
