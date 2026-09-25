#!/usr/bin/env python3
"""Independent reference for harbor tug berth contract (verifier only)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from itertools import combinations
from pathlib import Path


def parse_mmsi_from_vdm(sentence: str) -> int:
    """Contract-correct MMSI extraction from simplified VDM."""
    parts = sentence.split(",")
    if len(parts) < 6:
        raise ValueError("short vdm")
    payload = parts[5]
    if len(payload) < 17:
        raise ValueError("short payload")
    digits = payload[8:17]
    if not digits.isdigit():
        raise ValueError("non-digit mmsi")
    return int(digits)


def idempotency_key(voyage_id: str, berth_id: str, arrival_utc: str) -> str:
    return f"{voyage_id}:{berth_id}:{arrival_utc}"


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def dwell_minutes(arrival: str, departure: str) -> int:
    start = _parse_ts(arrival)
    end = _parse_ts(departure)
    return max(0, int((end - start).total_seconds() // 60))


def intersect_minutes(a: dict, b: dict) -> int:
    start = max(_parse_ts(a["arrival_utc"]), _parse_ts(b["arrival_utc"]))
    end = min(_parse_ts(a["departure_utc"]), _parse_ts(b["departure_utc"]))
    if end <= start:
        return 0
    return int((end - start).total_seconds() // 60)


def concurrent_overlap_minutes(rows: list[dict], berth_id: str) -> int:
    berth_rows = [r for r in rows if r["berth_id"] == berth_id]
    total = 0
    for a, b in combinations(berth_rows, 2):
        total += intersect_minutes(a, b)
    return total


def canonical_snapshot_bytes(rows: list[dict]) -> bytes:
    """Sorted snapshot rows with stable per-object key order."""
    sorted_rows = sorted(
        rows,
        key=lambda r: (r["berth_id"], r["arrival_utc"], r["voyage_id"]),
    )
    canon = []
    for r in sorted_rows:
        canon.append(
            {
                "arrival_utc": r["arrival_utc"],
                "berth_id": r["berth_id"],
                "departure_utc": r["departure_utc"],
                "mmsi": r["mmsi"],
                "voyage_id": r["voyage_id"],
            }
        )
    return json.dumps(canon, separators=(",", ":")).encode("utf-8")


def staging_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest_simulation(jsonl_path: Path) -> tuple[list[dict], int, int]:
    """Simulate contract-correct ingest into snapshot rows + replay stats."""
    accepted_rows: list[dict] = []
    seen: set[str] = set()
    accepted = 0
    duplicate = 0
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        parsed = parse_mmsi_from_vdm(row["nmea_raw"])
        if parsed != row["mmsi"]:
            raise ValueError("mmsi mismatch")
        key = idempotency_key(row["voyage_id"], row["berth_id"], row["arrival_utc"])
        if key in seen:
            duplicate += 1
            continue
        seen.add(key)
        accepted += 1
        accepted_rows.append(
            {
                "voyage_id": row["voyage_id"],
                "mmsi": row["mmsi"],
                "berth_id": row["berth_id"],
                "arrival_utc": row["arrival_utc"],
                "departure_utc": row["departure_utc"],
            }
        )
    return accepted_rows, accepted, duplicate


def build_expected_report(rows: list[dict], accepted: int, duplicate: int, snap_path: Path) -> dict:
    by_berth: dict[str, list[dict]] = {}
    for r in rows:
        by_berth.setdefault(r["berth_id"], []).append(r)
    berths = []
    for berth_id in sorted(by_berth):
        assignments = sorted(
            by_berth[berth_id],
            key=lambda r: (r["arrival_utc"], r["voyage_id"]),
        )
        dwell = sum(dwell_minutes(a["arrival_utc"], a["departure_utc"]) for a in assignments)
        overlap = concurrent_overlap_minutes(rows, berth_id)
        berths.append(
            {
                "berth_id": berth_id,
                "concurrent_overlap_minutes": overlap,
                "total_dwell_minutes": dwell,
                "assignments": [
                    {
                        "voyage_id": a["voyage_id"],
                        "mmsi": a["mmsi"],
                        "arrival_utc": a["arrival_utc"],
                        "departure_utc": a["departure_utc"],
                    }
                    for a in assignments
                ],
            }
        )
    return {
        "berths": berths,
        "replay_stats": {"accepted": accepted, "duplicate_rejected": duplicate},
        "staging_digest": staging_digest(snap_path),
    }
