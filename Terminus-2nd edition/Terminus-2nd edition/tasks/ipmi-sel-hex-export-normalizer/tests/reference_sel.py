#!/usr/bin/env python3
"""Independent reference parser for IPMI SEL contract (verifier only)."""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DOC_EXTRA_TYPES = {
    0xC0: "OEM Power Unit",
    0xC1: "OEM Memory Channel",
    0xDC: "Platform Security",
}

SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}


@dataclass
class SelRecord:
    record_id: int
    record_type: int
    timestamp: int
    generator_id: int
    sensor_type: int
    sensor_number: int
    event_type: int
    severity: str
    sensor_name: str


def xor_bytes(data: bytes) -> int:
    x = 0
    for b in data:
        x ^= b
    return x & 0xFF


def load_sensor_tsv(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, name = line.split("\t", 1)
        mapping[key.strip().lower()] = name.strip()
    return mapping


def sensor_name(sensor_type: int, tsv: dict[str, str]) -> str:
    hex_key = f"0x{sensor_type:02x}"
    if hex_key in tsv:
        return tsv[hex_key]
    if sensor_type in DOC_EXTRA_TYPES:
        return DOC_EXTRA_TYPES[sensor_type]
    return "unknown"


def severity_for_event_type(event_type: int) -> str:
    if event_type in (0x01, 0x02, 0x03):
        return "critical"
    if event_type in (0x06, 0x07, 0x08):
        return "warning"
    return "info"


def parse_header(blob: bytes) -> tuple[int, int]:
    if blob[:4] != b"SEL1":
        raise ValueError("bad magic")
    count, rec_len = struct.unpack_from("<HB", blob, 4)
    if xor_bytes(blob[:7]) != blob[7]:
        raise ValueError("bad header xor")
    return count, rec_len


def parse_record(blob: bytes, offset: int) -> SelRecord:
    rid, rtype, ts, gen, rev, stype, snum, edir, ed1, ed2 = struct.unpack_from(
        "<HBIHBBBBBB", blob, offset
    )
    body = blob[offset : offset + 15]
    stored = blob[offset + 15]
    if xor_bytes(body) != stored:
        raise ValueError("bad record xor")
    event_type = edir & 0x0F
    sev = severity_for_event_type(event_type)
    return SelRecord(
        record_id=rid,
        record_type=rtype,
        timestamp=ts,
        generator_id=gen,
        sensor_type=stype,
        sensor_number=snum,
        event_type=event_type,
        severity=sev,
        sensor_name="",
    )


def ingest_simulation(
    blob: bytes,
    tsv_path: Path,
    existing_ids: set[int] | None = None,
) -> tuple[list[SelRecord], int, int, int]:
    """Return accepted records, rejected_checksum, duplicate_rejected, accepted_count."""
    tsv = load_sensor_tsv(tsv_path)
    seen = set(existing_ids or ())
    accepted: list[SelRecord] = []
    rejected = 0
    dup = 0
    count, rec_len = parse_header(blob)
    offset = 8
    for _ in range(count):
        rtype = blob[offset + 2]
        if rtype != 0x02:
            offset += rec_len
            continue
        try:
            rec = parse_record(blob, offset)
        except ValueError:
            rejected += 1
            offset += rec_len
            continue
        if rec.record_id in seen:
            dup += 1
            offset += rec_len
            continue
        rec.sensor_name = sensor_name(rec.sensor_type, tsv)
        accepted.append(rec)
        seen.add(rec.record_id)
        offset += rec_len
    return accepted, rejected, dup, len(accepted)


def ts_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def export_rows(records: list[SelRecord]) -> list[dict[str, str]]:
    rows = []
    for rec in records:
        rows.append(
            {
                "record_id": str(rec.record_id),
                "timestamp_iso": ts_iso(rec.timestamp),
                "sensor_type_hex": f"0x{rec.sensor_type:02X}",
                "sensor_name": rec.sensor_name,
                "severity": rec.severity,
                "event_type_hex": f"0x{rec.event_type:02X}",
                "_rank": SEVERITY_RANK[rec.severity],
                "_ts": rec.timestamp,
                "_rid": rec.record_id,
            }
        )
    rows.sort(key=lambda r: (r["_rank"], r["_ts"], r["_rid"]))
    for r in rows:
        del r["_rank"]
        del r["_ts"]
        del r["_rid"]
    return rows


def build_expected_csv(records: list[SelRecord]) -> str:
    header = "record_id,timestamp_iso,sensor_type_hex,sensor_name,severity,event_type_hex"
    lines = [header]
    for row in export_rows(records):
        lines.append(
            ",".join(
                [
                    row["record_id"],
                    row["timestamp_iso"],
                    row["sensor_type_hex"],
                    row["sensor_name"],
                    row["severity"],
                    row["event_type_hex"],
                ]
            )
        )
    return "\n".join(lines) + "\n"


def staging_snapshot(accepted: int, rejected: int, dup: int, blob: bytes) -> dict:
    return {
        "accepted": accepted,
        "duplicate_rejected": dup,
        "ingest_digest": hashlib.sha256(blob).hexdigest(),
        "rejected_checksum": rejected,
    }


def canonical_stage_bytes(doc: dict) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def severity_ranks_from_csv(text: str) -> list[int]:
    lines = [ln for ln in text.strip().splitlines() if ln and not ln.startswith("record_id")]
    ranks = []
    for ln in lines:
        sev = ln.split(",")[4]
        ranks.append(SEVERITY_RANK[sev])
    return ranks
