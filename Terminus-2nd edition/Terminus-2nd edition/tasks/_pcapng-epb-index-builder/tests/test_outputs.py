#!/usr/bin/env python3
"""Verifier tests for pcap-index ingest/export pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_pcapng import (
    build_export_summary,
    canonical_index_bytes,
    ingest_capture,
    shift_capture_timestamps,
)

APP = Path("/app")
BIN = APP / "bin" / "pcap-index"
FIXTURES = APP / "fixtures"
HIDDEN = Path(__file__).resolve().parent / "hidden"
STATE = APP / "state"
OUTPUT = APP / "output"
INDEX = STATE / "pcap.idx"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _fresh_db() -> Path:
    STATE.mkdir(parents=True, exist_ok=True)
    db = STATE / f"index-{os.urandom(4).hex()}.db"
    if db.exists():
        db.unlink()
    return db


def _ingest_export(capture: Path, db: Path | None = None) -> Path:
    db_path = db or _fresh_db()
    out_path = OUTPUT / f"summary-{os.urandom(4).hex()}.json"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ingest = _run([str(BIN), "ingest", "--input", str(capture), "--db", str(db_path)])
    assert ingest.returncode == 0, ingest.stderr
    export = _run([str(BIN), "export", "--db", str(db_path), "--out", str(out_path)])
    assert export.returncode == 0, export.stderr
    return out_path


def _expected(capture: Path, ts_offset: int = 0) -> tuple[dict, bytes]:
    rows, names, crc_rej, dup_rej = ingest_capture(capture, ts_offset=ts_offset)
    index_bytes = canonical_index_bytes(rows)
    summary = build_export_summary(rows, names, crc_rej, dup_rej, index_bytes)
    return summary, index_bytes


class TestPcapIndexPipeline:
    """End-to-end ingest and export against independent PCAPng block walker."""

    def test_lan_single_index_and_summary(self) -> None:
        """Single-interface capture indexes every EPB with CRC options."""
        capture = FIXTURES / "lan_single.pcapng"
        report_path = _ingest_export(capture)
        actual = json.loads(report_path.read_text(encoding="utf-8"))
        expected, index_bytes = _expected(capture)
        assert INDEX.read_bytes() == index_bytes
        assert actual["packet_count"] == expected["packet_count"] == 3
        assert actual["interfaces"] == expected["interfaces"]
        assert actual["crc_rejected"] == expected["crc_rejected"] == 0
        assert actual["index_digest"] == hashlib.sha256(index_bytes).hexdigest()

    def test_dual_iface_unique_timestamp_count(self) -> None:
        """Shared timestamp on two interfaces counts once in packet_count."""
        capture = FIXTURES / "dual_iface.pcapng"
        report_path = _ingest_export(capture)
        actual = json.loads(report_path.read_text(encoding="utf-8"))
        expected, index_bytes = _expected(capture)
        assert INDEX.read_bytes() == index_bytes
        assert actual["packet_count"] == expected["packet_count"] == 3
        assert actual["interfaces"][0]["packet_count"] == 2
        assert actual["interfaces"][1]["packet_count"] == 2
        assert actual["duplicate_rejected"] == 0

    def test_crc_reject_not_indexed(self) -> None:
        """Bad EPB CRC must increment crc_rejected and stay out of the index."""
        capture = FIXTURES / "crc_trap.pcapng"
        report_path = _ingest_export(capture)
        actual = json.loads(report_path.read_text(encoding="utf-8"))
        expected, index_bytes = _expected(capture)
        assert INDEX.read_bytes() == index_bytes
        assert actual["crc_rejected"] == expected["crc_rejected"] == 1
        assert actual["packet_count"] == 2
        lines = INDEX.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

    def test_hidden_triple_iface_shifted(self) -> None:
        """Three-interface hidden capture with timestamp offset anti-hardcoding."""
        if not (HIDDEN / "triple_iface.pcapng").exists():
            pytest.skip("hidden fixture missing")
        offset = int(os.environ.get("TB3_TS_OFFSET", "424242"))
        shifted = Path(tempfile.mkdtemp()) / "shifted.pcapng"
        shift_capture_timestamps(HIDDEN / "triple_iface.pcapng", shifted, offset)
        try:
            report_path = _ingest_export(shifted)
            actual = json.loads(report_path.read_text(encoding="utf-8"))
            expected, index_bytes = _expected(shifted)
            assert INDEX.read_bytes() == index_bytes
            assert actual["packet_count"] == expected["packet_count"] == 3
            assert len(actual["interfaces"]) == 3
            assert actual["interfaces"][2]["if_name"] == "mgmt"
            assert actual["index_digest"] == hashlib.sha256(index_bytes).hexdigest()
        finally:
            shutil.rmtree(shifted.parent)

    def test_replay_duplicate_rejected(self) -> None:
        """Re-ingesting the same capture must not duplicate index rows."""
        capture = FIXTURES / "lan_single.pcapng"
        db = _fresh_db()
        _ingest_export(capture, db=db)
        first = INDEX.read_bytes()
        _ingest_export(capture, db=db)
        second = INDEX.read_bytes()
        assert first == second
        out_path = _ingest_export(capture, db=db)
        actual = json.loads(out_path.read_text(encoding="utf-8"))
        assert actual["duplicate_rejected"] >= 3
