#!/usr/bin/env python3
"""Behavioral verifier for harbor-tug-berth-allocator-cli."""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path

from reference_nmea import (
    build_expected_report,
    canonical_snapshot_bytes,
    ingest_simulation,
    parse_mmsi_from_vdm,
)

BIN = Path("/app/bin/tug-berth")
STATE = Path("/app/state")
OUTPUT = Path("/app/output")
FIXTURES = Path("/app/fixtures")
HIDDEN = Path("/tmp/verifier-fixtures/harbor-tug")


def _run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=cwd)


def _reset_state() -> None:
    if STATE.exists():
        shutil.rmtree(STATE)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    STATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)


def _ingest_export(jsonl: Path, db: Path | None = None) -> Path:
    db_path = db or STATE / "berth.db"
    _run([str(BIN), "ingest", "--input", str(jsonl), "--db", str(db_path)])
    out = OUTPUT / "berth-report.json"
    _run([str(BIN), "export", "--db", str(db_path), "--out", str(out)])
    return out


class TestHarborTugBerthAllocator:
    """CLI ingest/export contract tests with independent reference math."""

    def test_binary_exists(self):
        """The tug-berth CLI must be installed."""
        assert BIN.is_file(), "missing /app/bin/tug-berth"

    def test_alpha_bundle_ingest_export(self):
        """Bundled alpha JSONL produces contract report with overlap on B-12."""
        _reset_state()
        report_path = _ingest_export(FIXTURES / "events_alpha.jsonl")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        rows, acc, dup = ingest_simulation(FIXTURES / "events_alpha.jsonl")
        snap = STATE / "ingest-snapshot.json"
        assert snap.is_file(), "ingest must write staging snapshot"
        expected = build_expected_report(rows, acc, dup, snap)
        assert report["replay_stats"] == expected["replay_stats"]
        assert report["staging_digest"] == expected["staging_digest"]
        b12 = next(b for b in report["berths"] if b["berth_id"] == "B-12")
        assert b12["concurrent_overlap_minutes"] == 15
        assert b12["total_dwell_minutes"] == 60

    def test_staging_snapshot_canonical_bytes(self):
        """Staging file bytes must match canonical sorted-key JSON."""
        _reset_state()
        _ingest_export(FIXTURES / "events_alpha.jsonl")
        snap = STATE / "ingest-snapshot.json"
        rows, _, _ = ingest_simulation(FIXTURES / "events_alpha.jsonl")
        expected_bytes = canonical_snapshot_bytes(rows)
        assert snap.read_bytes() == expected_bytes

    def test_mmsi_parse_matches_row(self):
        """Ingest rejects or accepts rows only when NMEA MMSI matches row field."""
        _reset_state()
        suffix = uuid.uuid4().hex[:6]
        hidden = HIDDEN / f"events_mmsi_{suffix}.jsonl"
        HIDDEN.mkdir(parents=True, exist_ok=True)
        mmsi = 412345678
        payload = "00000000" + str(mmsi)
        line = {
            "voyage_id": f"V-HID-{suffix}",
            "mmsi": mmsi,
            "berth_id": "D-01",
            "arrival_utc": "2024-08-01T09:00:00Z",
            "departure_utc": "2024-08-01T09:30:00Z",
            "nmea_raw": f"!AIVDM,1,1,,A,{payload},0*AB",
        }
        hidden.write_text(json.dumps(line) + "\n", encoding="utf-8")
        report_path = _ingest_export(hidden)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        parsed = parse_mmsi_from_vdm(line["nmea_raw"])
        assert parsed == mmsi
        assert report["replay_stats"]["accepted"] == 1

    def test_idempotency_voyage_segment(self):
        """Duplicate replay must key on voyage_id plus berth and arrival."""
        _reset_state()
        suffix = uuid.uuid4().hex[:6]
        path = HIDDEN / f"events_replay_{suffix}.jsonl"
        HIDDEN.mkdir(parents=True, exist_ok=True)
        base = {
            "mmsi": 366999712,
            "berth_id": "E-03",
            "arrival_utc": "2024-09-01T12:00:00Z",
            "departure_utc": "2024-09-01T12:30:00Z",
            "nmea_raw": "!AIVDM,1,1,,A,00000000366999712,0*1F",
        }
        rows = [
            {**base, "voyage_id": f"V1-{suffix}"},
            {**base, "voyage_id": f"V1-{suffix}"},
            {**base, "voyage_id": f"V2-{suffix}", "departure_utc": "2024-09-01T12:40:00Z"},
        ]
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        report_path = _ingest_export(path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["replay_stats"]["accepted"] == 2
        assert report["replay_stats"]["duplicate_rejected"] == 1

    def test_duplicate_does_not_increment_accepted(self):
        """duplicate_rejected must not also bump accepted counter."""
        _reset_state()
        report_path = _ingest_export(FIXTURES / "events_alpha.jsonl")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["replay_stats"]["accepted"] == 3
        assert report["replay_stats"]["duplicate_rejected"] == 1
        assert report["replay_stats"]["accepted"] == 3, "duplicate handling must not inflate accepted"

    def test_beta_overlap_hidden(self):
        """Hidden beta fixture overlap minutes on C-02."""
        _reset_state()
        suffix = uuid.uuid4().hex[:8]
        src = FIXTURES / "events_beta.jsonl"
        hidden = HIDDEN / f"events_beta_{suffix}.jsonl"
        HIDDEN.mkdir(parents=True, exist_ok=True)
        lines = []
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            obj["voyage_id"] = obj["voyage_id"] + "-" + suffix
            lines.append(json.dumps(obj))
        hidden.write_text("\n".join(lines) + "\n", encoding="utf-8")
        report_path = _ingest_export(hidden)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        c02 = next(b for b in report["berths"] if b["berth_id"] == "C-02")
        assert c02["concurrent_overlap_minutes"] == 15

    def test_export_not_decoy_merge_max(self):
        """Concurrent overlap must be pairwise sum, not max dwell."""
        _reset_state()
        report_path = _ingest_export(FIXTURES / "events_beta.jsonl")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        c02 = next(b for b in report["berths"] if b["berth_id"] == "C-02")
        assert c02["concurrent_overlap_minutes"] != 25
        assert c02["concurrent_overlap_minutes"] == 15

    def test_staging_digest_from_file_bytes(self):
        """Export staging_digest must hash on-disk snapshot, not CSV summary."""
        _reset_state()
        report_path = _ingest_export(FIXTURES / "events_alpha.jsonl")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        snap = STATE / "ingest-snapshot.json"
        import hashlib

        expected = hashlib.sha256(snap.read_bytes()).hexdigest()
        assert report["staging_digest"] == expected

    def test_fresh_db_per_export_isolation(self):
        """Second ingest on clean DB must not inherit prior replay stats."""
        _reset_state()
        db = STATE / "isolated.db"
        _ingest_export(FIXTURES / "events_beta.jsonl", db=db)
        report = json.loads((OUTPUT / "berth-report.json").read_text(encoding="utf-8"))
        assert report["replay_stats"]["accepted"] == 2

    def test_rebuild_from_source_before_cli(self):
        """Verifier rebuilds the CLI from Go sources instead of relying on a stale image binary."""
        _reset_state()
        if BIN.exists():
            BIN.unlink()
        _run(["go", "build", "-o", "/app/bin/tug-berth", "./cmd/tug-berth"], cwd="/app")
        assert BIN.is_file()
        report_path = _ingest_export(FIXTURES / "events_beta.jsonl")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["replay_stats"]["accepted"] == 2

    def test_berth_sort_order(self):
        """Export berths sorted by berth_id ascending."""
        _reset_state()
        report_path = _ingest_export(FIXTURES / "events_alpha.jsonl")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        ids = [b["berth_id"] for b in report["berths"]]
        assert ids == sorted(ids)

    def test_assignment_sort_within_berth(self):
        """Assignments sorted by arrival then voyage_id."""
        _reset_state()
        report_path = _ingest_export(FIXTURES / "events_alpha.jsonl")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        b12 = next(b for b in report["berths"] if b["berth_id"] == "B-12")
        arrivals = [a["arrival_utc"] for a in b12["assignments"]]
        assert arrivals == sorted(arrivals)
