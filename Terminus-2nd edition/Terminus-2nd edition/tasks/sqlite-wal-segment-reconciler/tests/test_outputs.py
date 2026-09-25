"""Behavioral verifier for sqlite-wal-segment-reconciler."""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from reference_wal import (
    applied_count,
    distinct_applied_count,
    entry_count,
    make_wal_database,
    parse_wal_header,
    valid_frame_count,
)

BIN = Path("/app/bin/wal-chain")
STATE = Path("/app/state")
OUTPUT = Path("/app/output")
FIXTURES = Path("/app/fixtures")
SEED = FIXTURES / "seed"
TB3_HIDDEN = Path("/opt/verifier-fixtures/wal/hidden")
OPT_HIDDEN = Path("/opt/verifier-fixtures/wal/hidden")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _copy_db_tree(src_db: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_db = dest_dir / src_db.name
    shutil.copy2(src_db, dest_db)
    src_parent = src_db.parent
    for extra in (f"{src_db.name}-wal", f"{src_db.name}-shm", f"{src_db.name}.wal.snap", f"{src_db.name}.shm.snap"):
        src = src_parent / extra
        if src.exists():
            shutil.copy2(src, dest_dir / extra)
    wal = dest_dir / f"{dest_db.name}-wal"
    snap = dest_dir / f"{dest_db.name}.wal.snap"
    if not wal.exists() and snap.exists():
        shutil.copy2(snap, wal)
    return dest_db


def _wal_path(db: Path) -> Path:
    wal = db.parent / f"{db.name}-wal"
    snap = db.parent / f"{db.name}.wal.snap"
    if not wal.exists() and snap.exists():
        return snap
    return wal


def _chain(db: Path) -> Path:
    _run([str(BIN), "reconcile", "--db", str(db)])
    _run([str(BIN), "stage", "--db", str(db)])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out = OUTPUT / f"wal-report-{uuid.uuid4().hex[:8]}.json"
    _run([str(BIN), "export", "--db", str(db), "--out", str(out)])
    return out


def _compact_export_json(applied: int, entry_rows: int, page_size: int) -> str:
    """Expected wal-report.json: sorted keys, compact separators, trailing newline."""
    doc = {
        "applied_frame_count": applied,
        "entry_row_count": entry_rows,
        "page_size": page_size,
    }
    return json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n"


def _assert_export_format(report_path: Path, *, page_size: int, applied: int, entry_rows: int) -> dict:
    raw = report_path.read_text(encoding="utf-8")
    assert raw == _compact_export_json(applied, entry_rows, page_size), "export must be sorted compact JSON"
    report = json.loads(raw)
    assert report["page_size"] == page_size
    assert report["applied_frame_count"] == applied
    assert report["entry_row_count"] == entry_rows
    return report


def _compact_staging_json(page_size: int, frame_count: int, salt1: int, salt2: int) -> str:
    doc = {
        "frame_count": frame_count,
        "page_size": page_size,
        "salt1": salt1,
        "salt2": salt2,
    }
    return json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n"


def _assert_staging_snapshot(stage_path: Path, hdr) -> dict:
    """Staging snapshot must be compact sorted JSON beside the database."""
    raw = stage_path.read_text(encoding="utf-8")
    expected = _compact_staging_json(hdr.page_size, hdr.frame_count, hdr.salt1, hdr.salt2)
    assert raw == expected, "staging snapshot must use sorted compact JSON"
    return json.loads(raw)


class TestWalChainPipeline:
    """WAL reconcile, stage snapshot, and export report via wal-chain CLI."""

    def test_binary_exists(self):
        """wal-chain CLI is installed at /app/bin/wal-chain."""
        assert BIN.is_file(), "missing /app/bin/wal-chain"

    def test_example_workflow_paths(self):
        """Instruction example writes /app/state/wal.stage and /app/output/wal-report.json"""
        db = Path("/app/state/ledger.db")
        stage = Path("/app/state/wal.stage")
        export = Path("/app/output/wal-report.json")
        assert db.is_file(), "seed ledger at /app/state/ledger.db"
        if stage.exists():
            stage.unlink()
        if export.exists():
            export.unlink()
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        expected_applied = valid_frame_count(wal)
        _run([str(BIN), "reconcile", "--db", str(db)])
        _run([str(BIN), "stage", "--db", str(db)])
        _run([str(BIN), "export", "--db", str(db), "--out", str(export)])
        assert stage.is_file(), "stage must write /app/state/wal.stage"
        assert export.is_file(), "export must write /app/output/wal-report.json"
        _assert_export_format(
            export,
            page_size=hdr.page_size,
            applied=expected_applied,
            entry_rows=entry_count(db),
        )

    def test_packaged_ledger_checksum_invariants(self):
        """Bundled ledger WAL reconciles with matching salts and counts."""
        work = STATE / f"seed_{uuid.uuid4().hex[:8]}"
        db = _copy_db_tree(SEED / "ledger.db", work)
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        expected_applied = valid_frame_count(wal)
        report_path = _chain(db)
        stage = db.parent / "wal.stage"
        assert stage.is_file(), "stage must write wal.stage beside db"
        staged = json.loads(stage.read_text(encoding="utf-8"))
        assert staged["page_size"] == hdr.page_size
        assert staged["frame_count"] == hdr.frame_count
        assert staged["salt1"] == hdr.salt1
        assert staged["salt2"] == hdr.salt2
        rows = entry_count(db)
        assert applied_count(db) == expected_applied
        assert distinct_applied_count(db) == expected_applied
        _assert_export_format(
            report_path,
            page_size=hdr.page_size,
            applied=expected_applied,
            entry_rows=rows,
        )

    def test_unique_salt_hidden_case(self, tmp_path: Path):
        """Hidden rows produce a WAL whose salts differ per generated case."""
        suffix = uuid.uuid4().hex
        rows = [(f"SKU-{suffix}-{i}", i + 1) for i in range(4)]
        db = make_wal_database(tmp_path / f"case_{suffix}", rows)
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        expected = valid_frame_count(wal)
        report_path = _chain(db)
        staged = json.loads((db.parent / "wal.stage").read_text(encoding="utf-8"))
        assert staged["salt1"] == hdr.salt1
        assert staged["salt2"] == hdr.salt2
        _assert_export_format(
            report_path,
            page_size=hdr.page_size,
            applied=expected,
            entry_rows=len(rows),
        )

    def test_duplicate_reconcile_stable_applied_rows(self, tmp_path: Path):
        """Second reconcile must not grow _wal_applied row count."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(
            tmp_path / f"idempotent_{suffix}",
            [(f"IDEM-{suffix}", 7), (f"IDEM-{suffix}-b", 2)],
        )
        _run([str(BIN), "reconcile", "--db", str(db)])
        first = applied_count(db)
        _run([str(BIN), "reconcile", "--db", str(db)])
        second = applied_count(db)
        assert second == first
        assert distinct_applied_count(db) == first

    def test_report_counts_applied_rows_not_peak_frame(self, tmp_path: Path):
        """applied_frame_count tracks _wal_applied rows, not max frame index."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(
            tmp_path / f"export_{suffix}",
            [(f"EXP-{suffix}-{i}", i) for i in range(3)],
        )
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        expected = valid_frame_count(wal)
        _run([str(BIN), "reconcile", "--db", str(db)])
        _run([str(BIN), "stage", "--db", str(db)])
        out = tmp_path / f"report_{suffix}.json"
        _run([str(BIN), "export", "--db", str(db), "--out", str(out)])
        applied = applied_count(db)
        assert applied == expected
        _assert_export_format(
            out,
            page_size=hdr.page_size,
            applied=applied,
            entry_rows=3,
        )

    def test_crc_mismatch_blocks_frame_insertion(self, tmp_path: Path):
        """Invalid frame checksum aborts without inserting that frame."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(tmp_path / f"badsum_{suffix}", [(f"BAD-{suffix}", 1)])
        wal = db.parent / f"{db.name}-wal"
        data = bytearray(wal.read_bytes())
        hdr = parse_wal_header(wal)
        if hdr.frame_count < 1:
            pytest.skip("no frames")
        frame_off = 32 + 0 * (24 + hdr.page_size)
        data[frame_off + 16] ^= 0xFF
        wal.write_bytes(data)
        snap = db.parent / f"{db.name}.wal.snap"
        if snap.exists():
            snap.unlink()
        proc = _run([str(BIN), "reconcile", "--db", str(db)], check=False)
        assert proc.returncode != 0
        try:
            count = applied_count(db)
        except Exception:
            count = 0
        assert count < hdr.frame_count

    def test_sidecar_fields_on_custom_db_path(self, tmp_path: Path):
        """Staging snapshot beside a non-/app/state database includes salts and page_size."""
        suffix = uuid.uuid4().hex[:8]
        db = make_wal_database(tmp_path / f"custom_{suffix}", [(f"CUS-{suffix}", 3)])
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        _run([str(BIN), "reconcile", "--db", str(db)])
        _run([str(BIN), "stage", "--db", str(db)])
        stage = db.parent / "wal.stage"
        staged = _assert_staging_snapshot(stage, hdr)
        assert staged["page_size"] == hdr.page_size
        assert staged["frame_count"] == hdr.frame_count

    def test_export_blocked_without_sidecar_file(self, tmp_path: Path):
        """Export fails when staging snapshot is missing beside the database."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(tmp_path / f"nostage_{suffix}", [(f"NS-{suffix}", 1)])
        _run([str(BIN), "reconcile", "--db", str(db)])
        stage = db.parent / "wal.stage"
        if stage.exists():
            stage.unlink()
        out = tmp_path / "report.json"
        proc = _run([str(BIN), "export", "--db", str(db), "--out", str(out)], check=False)
        assert proc.returncode != 0

    def test_wal_ingest_restores_snap_when_sidecar_missing(self, tmp_path: Path):
        """WAL ingest path restores .wal.snap when db-wal sidecar is absent."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(tmp_path / f"ingest_{suffix}", [(f"ING-{suffix}", 2)])
        wal = db.parent / f"{db.name}-wal"
        snap = db.parent / f"{db.name}.wal.snap"
        assert snap.is_file()
        wal.unlink()
        assert not wal.exists()
        _run([str(BIN), "reconcile", "--db", str(db)])
        assert applied_count(db) == valid_frame_count(snap)

    def test_page_size_read_from_wal_offset_eight(self, tmp_path: Path):
        """Frame math uses page size at WAL header offset 8."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(tmp_path / f"psz_{suffix}", [(f"PSZ-{suffix}-{i}", i) for i in range(2)])
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        assert hdr.page_size == 4096
        assert hdr.frame_count == valid_frame_count(wal)

    def test_distinct_applied_matches_row_count(self, tmp_path: Path):
        """Every applied frame_id is unique in _wal_applied."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(
            tmp_path / f"distinct_{suffix}",
            [(f"D-{suffix}-{i}", i) for i in range(5)],
        )
        wal = _wal_path(db)
        expected = valid_frame_count(wal)
        _run([str(BIN), "reconcile", "--db", str(db)])
        total = applied_count(db)
        distinct = distinct_applied_count(db)
        assert total == distinct == expected

    def test_export_page_size_matches_staging_snapshot(self, tmp_path: Path):
        """Export page_size equals staging snapshot and WAL header."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(tmp_path / f"pagesz_{suffix}", [(f"P-{suffix}", 8)])
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        report_path = _chain(db)
        staged = json.loads((db.parent / "wal.stage").read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["page_size"] == staged["page_size"] == hdr.page_size

    def test_reconcile_then_stage_preserves_salt_pair(self, tmp_path: Path):
        """Staging snapshot salt1/salt2 match WAL header after reconcile."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(tmp_path / f"salt_{suffix}", [(f"S-{suffix}", 1)], salt1=0xDEADBEEF, salt2=0xCAFEBABE)
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        _run([str(BIN), "reconcile", "--db", str(db)])
        _run([str(BIN), "stage", "--db", str(db)])
        staged = _assert_staging_snapshot(db.parent / "wal.stage", hdr)
        assert staged["salt1"] == 0xDEADBEEF
        assert staged["salt2"] == 0xCAFEBABE

    def test_entry_row_count_tracks_entries_table(self, tmp_path: Path):
        """Export entry_row_count equals SELECT COUNT(*) FROM entries."""
        suffix = uuid.uuid4().hex[:10]
        rows = [(f"E-{suffix}-{i}", i + 1) for i in range(4)]
        db = make_wal_database(tmp_path / f"entries_{suffix}", rows)
        report_path = _chain(db)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["entry_row_count"] == len(rows)
        assert report["entry_row_count"] == entry_count(db)

    def test_tb3_hidden_verifier_fixture_reconcile(self, tmp_path: Path):
        """TB3 hidden /opt/verifier-fixtures WAL pair reconciles independently."""
        assert TB3_HIDDEN.is_dir(), "missing /opt/verifier-fixtures/wal/hidden"
        work = tmp_path / f"tb3_{uuid.uuid4().hex[:8]}"
        db = _copy_db_tree(TB3_HIDDEN / "ledger.db", work)
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        expected = valid_frame_count(wal)
        report_path = _chain(db)
        _assert_export_format(
            report_path,
            page_size=hdr.page_size,
            applied=expected,
            entry_rows=entry_count(db),
        )

    def test_opt_verifier_fixtures_staging_snapshot(self, tmp_path: Path):
        """Hidden opt verifier fixture staging snapshot matches WAL header salts."""
        hidden_root = Path("/opt/verifier-fixtures/wal/hidden")
        assert hidden_root.is_dir()
        assert OPT_HIDDEN.is_dir()
        work = tmp_path / f"opt_{uuid.uuid4().hex[:8]}"
        db = _copy_db_tree(OPT_HIDDEN / "ledger.db", work)
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        _run([str(BIN), "reconcile", "--db", str(db)])
        _run([str(BIN), "stage", "--db", str(db)])
        _assert_staging_snapshot(db.parent / "wal.stage", hdr)

    def test_frame_count_matches_valid_checksum_prefix(self, tmp_path: Path):
        """Applied count equals longest valid checksum prefix in WAL sidecar."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(
            tmp_path / f"prefix_{suffix}",
            [(f"PF-{suffix}-{i}", i) for i in range(3)],
        )
        wal = _wal_path(db)
        expected = valid_frame_count(wal)
        _run([str(BIN), "reconcile", "--db", str(db)])
        assert applied_count(db) == expected

    def test_wal_stage_snapshot_lf_terminated(self, tmp_path: Path):
        """Staging snapshot JSON ends with a trailing newline and compact separators."""
        suffix = uuid.uuid4().hex[:10]
        db = make_wal_database(tmp_path / f"nl_{suffix}", [(f"NL-{suffix}", 1)])
        wal = _wal_path(db)
        hdr = parse_wal_header(wal)
        _run([str(BIN), "reconcile", "--db", str(db)])
        _run([str(BIN), "stage", "--db", str(db)])
        raw = (db.parent / "wal.stage").read_text(encoding="utf-8")
        assert raw.endswith("\n")
        assert raw == _compact_staging_json(hdr.page_size, hdr.frame_count, hdr.salt1, hdr.salt2)
