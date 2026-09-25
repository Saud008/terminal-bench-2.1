#!/usr/bin/env python3
"""Behavioral verifier for ipmi-sel-hex-export-normalizer."""

from __future__ import annotations

import json
import shutil
import sqlite3
import struct
import subprocess
import uuid
from pathlib import Path

from reference_sel import (
    build_expected_csv,
    canonical_stage_bytes,
    ingest_simulation,
    severity_ranks_from_csv,
    staging_snapshot,
    xor_bytes,
)

BIN = Path("/app/bin/sel-chain")
STATE = Path("/app/state")
OUTPUT = Path("/app/output")
FIXTURES = Path("/app/fixtures")
TSV = Path("/app/config/sensor-types.tsv")
HIDDEN = Path("/tmp/sel_hidden_fixtures")


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def _reset_state() -> None:
    if STATE.exists():
        shutil.rmtree(STATE)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    STATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)


def _ingest_export(sel_bin: Path, db: Path | None = None) -> Path:
    db_path = db or STATE / "sel.db"
    _run([str(BIN), "ingest", "--input", str(sel_bin), "--db", str(db_path)])
    out = OUTPUT / "sel-events.csv"
    _run([str(BIN), "export", "--db", str(db_path), "--out", str(out)])
    return out


class TestSelChainContract:
    """SEL ingest/export contract tests with independent reference parsing."""

    def test_binary_exists(self):
        """The sel-chain CLI must be installed."""
        assert BIN.is_file(), "missing /app/bin/sel-chain"

    def test_alpha_severity_order_not_timestamp(self):
        """Critical events must sort before later warnings and info rows."""
        _reset_state()
        blob = (FIXTURES / "sel_alpha.bin").read_bytes()
        csv_path = _ingest_export(FIXTURES / "sel_alpha.bin")
        text = csv_path.read_text(encoding="utf-8")
        ranks = severity_ranks_from_csv(text)
        assert ranks == sorted(ranks), "export must sort by severity rank ascending"
        records, _, _, _ = ingest_simulation(blob, TSV)
        expected = build_expected_csv(records)
        assert text == expected

    def test_alpha_staging_counts(self):
        """Alpha ingest staging snapshot matches reference accepted count."""
        _reset_state()
        blob = (FIXTURES / "sel_alpha.bin").read_bytes()
        _ingest_export(FIXTURES / "sel_alpha.bin")
        stage = json.loads((STATE / "sel.stage").read_text(encoding="utf-8"))
        records, rej, dup, acc = ingest_simulation(blob, TSV)
        expected = staging_snapshot(acc, rej, dup, blob)
        assert stage == expected
        assert stage["accepted"] == 4
        assert stage["rejected_checksum"] == 0
        assert stage["duplicate_rejected"] == 0

    def test_sensor_names_from_hex_map(self):
        """Bundled TSV hex keys resolve processor and memory names."""
        _reset_state()
        csv_path = _ingest_export(FIXTURES / "sel_alpha.bin")
        lines = csv_path.read_text(encoding="utf-8").strip().splitlines()[1:]
        names = {ln.split(",")[0]: ln.split(",")[3] for ln in lines}
        assert names["2"] == "Memory"
        assert names["1"] == "Processor"

    def test_beta_oem_sensor_types_from_docs(self):
        """OEM sensor types documented only in ipmi-sel.md must resolve."""
        _reset_state()
        csv_path = _ingest_export(FIXTURES / "sel_beta.bin")
        text = csv_path.read_text(encoding="utf-8")
        assert "OEM Power Unit" in text
        assert "Platform Security" in text
        assert "OEM Memory Channel" in text

    def test_beta_checksum_rejects_bad_record(self):
        """Corrupt record_xor must not persist and increments rejected_checksum."""
        _reset_state()
        blob = (FIXTURES / "sel_beta.bin").read_bytes()
        _ingest_export(FIXTURES / "sel_beta.bin")
        stage = json.loads((STATE / "sel.stage").read_text(encoding="utf-8"))
        _, rej, _, acc = ingest_simulation(blob, TSV)
        assert stage["rejected_checksum"] == rej == 1
        assert stage["accepted"] == acc == 3
        conn = sqlite3.connect(STATE / "sel.db")
        try:
            rows = conn.execute("SELECT record_id FROM sel_records").fetchall()
        finally:
            conn.close()
        assert 14 not in {r[0] for r in rows}

    def test_replay_duplicate_record_ids(self):
        """Re-ingesting the same blob must dedupe by record_id."""
        _reset_state()
        db = STATE / "sel.db"
        _run([str(BIN), "ingest", "--input", str(FIXTURES / "sel_alpha.bin"), "--db", str(db)])
        _run([str(BIN), "ingest", "--input", str(FIXTURES / "sel_alpha.bin"), "--db", str(db)])
        stage = json.loads((STATE / "sel.stage").read_text(encoding="utf-8"))
        assert stage["accepted"] == 0
        assert stage["duplicate_rejected"] == 4
        conn = sqlite3.connect(db)
        try:
            cnt = conn.execute("SELECT COUNT(*) FROM sel_records").fetchone()[0]
        finally:
            conn.close()
        assert cnt == 4

    def test_hidden_non_bundled_sensor_sort(self):
        """Hidden blob with doc-only sensor type keeps severity-first ordering."""
        _reset_state()
        HIDDEN.mkdir(parents=True, exist_ok=True)
        suffix = uuid.uuid4().hex[:8]

        def pack_record(rid, ts, stype, etype_nibble):
            edir = etype_nibble & 0x0F
            body = struct.pack(
                "<HBIHBBBBBB",
                rid,
                0x02,
                ts,
                0x0020,
                0x04,
                stype,
                0x01,
                edir,
                0,
                0,
            )
            return body + bytes([xor_bytes(body)])

        records = [
            pack_record(100, 1_700_200_100, 0xDC, 0x08),
            pack_record(101, 1_700_200_050, 0xC1, 0x01),
        ]
        header = b"SEL1" + struct.pack("<HB", len(records), 16)
        header += bytes([xor_bytes(header)])
        blob = header + b"".join(records)
        hidden = HIDDEN / f"sel_hidden_{suffix}.bin"
        hidden.write_bytes(blob)

        csv_path = _ingest_export(hidden)
        ranks = severity_ranks_from_csv(csv_path.read_text(encoding="utf-8"))
        assert ranks[0] < ranks[1], "critical must precede warning regardless of timestamp"
        assert "Platform Security" in csv_path.read_text(encoding="utf-8")
        assert "OEM Memory Channel" in csv_path.read_text(encoding="utf-8")

    def test_staging_canonical_bytes(self):
        """Staging JSON uses sorted keys and trailing newline."""
        _reset_state()
        blob = (FIXTURES / "sel_alpha.bin").read_bytes()
        _ingest_export(FIXTURES / "sel_alpha.bin")
        snap = STATE / "sel.stage"
        records, rej, dup, acc = ingest_simulation(blob, TSV)
        expected = staging_snapshot(acc, rej, dup, blob)
        assert snap.read_bytes() == canonical_stage_bytes(expected)

    def test_export_row_count_matches_db(self):
        """CSV data rows equal sel_records row count."""
        _reset_state()
        csv_path = _ingest_export(FIXTURES / "sel_alpha.bin")
        data_lines = [
            ln for ln in csv_path.read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("record_id")
        ]
        conn = sqlite3.connect(STATE / "sel.db")
        try:
            cnt = conn.execute("SELECT COUNT(*) FROM sel_records").fetchone()[0]
        finally:
            conn.close()
        assert len(data_lines) == cnt == 4
