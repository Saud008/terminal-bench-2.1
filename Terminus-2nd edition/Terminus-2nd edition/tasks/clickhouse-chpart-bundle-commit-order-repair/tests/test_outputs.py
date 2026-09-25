"""Black-box behavioral tests for the chparts MergeTree parts pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest

from reference_mergetree import (
    build_hidden_parts_dir,
    reference_export,
    write_part_bundle,
)

APP = Path("/app")
DB = APP / "data" / "parts.db"
CONFIG = APP / "config/table.json"
BUNDLED = APP / "fixtures" / "parts"
REPORT = APP / "output" / "parts-report.json"
SNAPSHOT = APP / "state" / "parts-snapshot.json"
MANIFEST = APP / "state" / "parts.manifest"
TTL_GRACE_MS = 86_400_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PROTECTED: dict[str, str] = {}
for rel in [
    "config/table.json",
    "docs/ingest-export-pipeline.md",
    "docs/part-bundle-format.md",
    "docs/merge-snapshot.md",
    "docs/commit-barrier.md",
    "docs/export-schema.md",
    "docs/go-module-api.md",
]:
    p = APP / rel
    if p.is_file():
        PROTECTED[rel] = sha256(p)
for p in sorted((APP / "fixtures").rglob("*")):
    if p.is_file():
        PROTECTED[str(p.relative_to(APP))] = sha256(p)


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, env=env, **kwargs)


def reset() -> None:
    proc = _run(["bash", str(APP / "scripts/reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def build() -> None:
    proc = _run(["go", "build", "-mod=readonly", "-o", "/usr/local/bin/chparts", "./cmd/chparts"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def ingest(parts_dir: Path) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "chparts",
            "ingest",
            "--parts-dir",
            str(parts_dir),
            "--config",
            str(CONFIG),
            "--db",
            str(DB),
        ]
    )


def export_report() -> subprocess.CompletedProcess[str]:
    return _run(["chparts", "export", "--output", str(REPORT)])


def read(parts_dir: Path) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "chparts",
            "read",
            "--parts-dir",
            str(parts_dir),
            "--config",
            str(CONFIG),
            "--db",
            str(DB),
            "--output",
            str(REPORT),
        ]
    )


@pytest.fixture(scope="module", autouse=True)
def _ready() -> None:
    reset()
    build()


def test_fixture_integrity() -> None:
    """Bundled fixtures and contract docs under /app were not modified."""
    current = {}
    for rel, expected in PROTECTED.items():
        current[rel] = sha256(APP / rel)
    assert current == PROTECTED


def test_bundled_read_matches_reference() -> None:
    """Bundled parts produce a report matching the independent reference decoder."""
    reset()
    proc = read(BUNDLED)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    got = json.loads(REPORT.read_text(encoding="utf-8"))
    expect = reference_export(BUNDLED)
    assert got == expect


def test_merge_prefers_higher_version() -> None:
    """Merge keeps the row with the highest ver for each primary key."""
    reset()
    read(BUNDLED)
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    row = next(r for r in snap["rows"] if r["id"] == "1")
    assert row["ver"] == 20
    assert row["value"] == "gamma"


def test_checksum_failure_not_committed(tmp_path: Path) -> None:
    """Invalid checksum aborts ingest and leaves the part uncommitted in SQLite."""
    reset()
    bad = tmp_path / "bad-part"
    shutil.copytree(BUNDLED / "part-01", bad)
    meta = json.loads((bad / "part.meta.json").read_text(encoding="utf-8"))
    meta["checksum"] = "sha256:00"
    (bad / "part.meta.json").write_text(json.dumps(meta), encoding="utf-8")
    proc = read(tmp_path)
    assert proc.returncode != 0
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT committed, checksum_ok FROM parts WHERE part_id=?", ("part-01",)).fetchone()
    conn.close()
    assert row == (0, 0)


def test_replay_is_idempotent() -> None:
    """Running read twice on the same parts dir yields an identical report."""
    reset()
    assert read(BUNDLED).returncode == 0
    first = json.loads(REPORT.read_text(encoding="utf-8"))
    assert read(BUNDLED).returncode == 0
    second = json.loads(REPORT.read_text(encoding="utf-8"))
    assert second == first


def test_export_reads_snapshot_not_manifest() -> None:
    """Export rows match the staged snapshot, not the legacy manifest scratch file."""
    reset()
    read(BUNDLED)
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(snap["rows"]) > 0
    assert man.get("rows") in (None, [])
    assert report["rows"] == snap["rows"]


def test_commit_barrier_fsync_before_max_block() -> None:
    """Commit log records fsync before publishing max_block from ingested parts."""
    reset()
    read(BUNDLED)
    conn = sqlite3.connect(DB)
    max_block, fsynced = conn.execute("SELECT max_block, fsynced FROM commit_log WHERE id=1").fetchone()
    conn.close()
    assert fsynced == 1
    assert max_block >= 7


def test_hidden_parts_match_reference(tmp_path: Path) -> None:
    """TB3_hidden tmp_path part bundles match the independent reference decoder."""
    reset()
    parts_dir = build_hidden_parts_dir(tmp_path / "hidden-parts")
    proc = read(parts_dir)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    got = json.loads(REPORT.read_text(encoding="utf-8"))
    expect = reference_export(parts_dir)
    assert got == expect


def test_table_suffix_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """CHPARTS_TABLE_SUFFIX selects the TB3_<suffix>_events table name in export."""
    monkeypatch.setenv("CHPARTS_TABLE_SUFFIX", "matrix-7")
    reset()
    read(BUNDLED)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["table_name"] == "TB3_matrix-7_events"


def test_export_subcommand_ignores_poisoned_manifest() -> None:
    """Export reads the snapshot even when the manifest scratch file contains trap rows."""
    reset()
    assert ingest(BUNDLED).returncode == 0
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    trap = {
        "table_suffix": snap["table_suffix"],
        "table_name": snap["table_name"],
        "max_block_number": snap["max_block_number"],
        "fsynced": snap["fsynced"],
        "parts": snap["parts"],
        "rows": [{"id": "trap", "ver": 99, "value": "manifest-only", "expire_ts": 9_999_999_999_999}],
    }
    MANIFEST.write_text(json.dumps(trap), encoding="utf-8")
    assert export_report().returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["rows"] == snap["rows"]
    assert all(r["id"] != "trap" for r in report["rows"])


def test_export_subcommand_ignores_sqlite_row_deletion() -> None:
    """Export still reflects the snapshot after SQLite row payloads are deleted."""
    reset()
    assert ingest(BUNDLED).returncode == 0
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM rows")
    conn.commit()
    conn.close()
    assert export_report().returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["rows"] == snap["rows"]
    assert report["row_count"] == len(snap["rows"])


def test_export_without_reingest_matches_prior_snapshot() -> None:
    """A second export call without ingest reproduces the same report from the snapshot."""
    reset()
    assert read(BUNDLED).returncode == 0
    first = json.loads(REPORT.read_text(encoding="utf-8"))
    assert export_report().returncode == 0
    second = json.loads(REPORT.read_text(encoding="utf-8"))
    assert second == first


def test_snapshot_rows_match_export_after_ingest_only() -> None:
    """Ingest then export yields report rows identical to parts-snapshot.json."""
    reset()
    assert ingest(BUNDLED).returncode == 0
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert export_report().returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["max_block_number"] == snap["max_block_number"]
    assert report["rows"] == snap["rows"]


def test_hidden_ttl_prunes_stale_row(tmp_path: Path) -> None:
    """TB3_hidden bundles drop expired merge winners after TTL grace pruning."""
    reset()
    parts = tmp_path / "ttl-expired-winner"
    future = int(time.time() * 1000) + TTL_GRACE_MS + 60_000
    expired = 1
    write_part_bundle(parts, "ttl-a", "batch-ttl", [("55", 3, "stale-low", future)])
    write_part_bundle(parts, "ttl-b", "batch-ttl", [("55", 10, "stale-high", expired)])
    proc = read(parts)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert snap["rows"] == []
    assert report["rows"] == []
    assert report["row_count"] == 0


def test_ttl_keeps_non_expired_merge_winner(tmp_path: Path) -> None:
    """TTL keeps the merged row when the winning expire_ts is still inside grace."""
    reset()
    parts = tmp_path / "ttl-fresh-winner"
    future = int(time.time() * 1000) + TTL_GRACE_MS + 60_000
    write_part_bundle(parts, "ttl-a", "batch-fresh", [("56", 2, "old-value", future)])
    write_part_bundle(parts, "ttl-b", "batch-fresh", [("56", 8, "new-value", future)])
    proc = read(parts)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(snap["rows"]) == 1
    assert snap["rows"][0]["ver"] == 8
    assert snap["rows"][0]["value"] == "new-value"
    assert report["rows"] == snap["rows"]


def test_ttl_drops_lower_version_before_merge_winner_checked(tmp_path: Path) -> None:
    """Expired lower-version rows do not block a fresher sibling from surviving TTL."""
    reset()
    parts = tmp_path / "ttl-mixed"
    future = int(time.time() * 1000) + TTL_GRACE_MS + 60_000
    write_part_bundle(parts, "ttl-a", "batch-mix", [("57", 1, "gone", 1)])
    write_part_bundle(parts, "ttl-b", "batch-mix", [("57", 4, "kept", future)])
    proc = read(parts)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(snap["rows"]) == 1
    assert snap["rows"][0]["ver"] == 4
    assert report["rows"] == snap["rows"]


def test_ttl_snapshot_and_report_stay_aligned(tmp_path: Path) -> None:
    """TTL pruning results in matching row_count across snapshot and export report."""
    reset()
    parts = tmp_path / "ttl-align"
    future = int(time.time() * 1000) + TTL_GRACE_MS + 60_000
    write_part_bundle(parts, "ttl-a", "batch-align", [("58", 5, "live", future), ("59", 1, "dead", 1)])
    proc = read(parts)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["row_count"] == len(snap["rows"])
    assert report["rows"] == snap["rows"]


def test_export_parts_sorted_by_part_id() -> None:
    """Export parts array is sorted ascending by part_id per export-schema.md."""
    reset()
    read(BUNDLED)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    part_ids = [p["part_id"] for p in report["parts"]]
    assert part_ids == sorted(part_ids)


def test_duplicate_batch_part_key_not_reingested(tmp_path: Path) -> None:
    """Replaying the same batch_id:part_id key does not duplicate merged rows."""
    reset()
    parts = tmp_path / "dup-key"
    shutil.copytree(BUNDLED / "part-01", parts / "part-01")
    assert read(parts).returncode == 0
    conn = sqlite3.connect(DB)
    first_count = conn.execute("SELECT COUNT(1) FROM rows").fetchone()[0]
    dup = parts / "part-01-dup"
    shutil.copytree(parts / "part-01", dup)
    assert read(parts).returncode == 0
    second_count = conn.execute("SELECT COUNT(1) FROM rows").fetchone()[0]
    conn.close()
    assert first_count > 0
    assert second_count == first_count
