"""Independent reference parser/builder for FIT lap fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

NOTE_CAP = 12
LAP_WIDTH = 24


def crc16(data: bytes) -> int:
    return sum(data) & 0xFFFF


def classify_trigger(code: int) -> str:
    return {
        0: "manual",
        1: "time",
        2: "distance",
        3: "session-end",
    }.get(code, "unknown")


def parse_fit(path: Path) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    if len(raw) < 8:
        raise ValueError("too short")
    if raw[:4] != b"FITL":
        raise ValueError("bad magic")
    if raw[4] != 1:
        raise ValueError("bad version")
    count = raw[5]
    payload_end = len(raw) - 2
    expected_crc = int.from_bytes(raw[payload_end:], "little")
    actual_crc = crc16(raw[:payload_end])
    if expected_crc != actual_crc:
        raise ValueError("crc mismatch")
    payload = raw[6:payload_end]
    if len(payload) != count * LAP_WIDTH:
        raise ValueError("length mismatch")

    laps: list[dict[str, Any]] = []
    for i in range(count):
        off = i * LAP_WIDTH
        row = payload[off : off + LAP_WIDTH]
        note_len = row[11]
        note = row[12 : 12 + note_len].decode("utf-8")
        laps.append(
            {
                "original_index": i,
                "start_time": int.from_bytes(row[0:4], "little"),
                "end_time": int.from_bytes(row[4:8], "little"),
                "distance_m": int.from_bytes(row[8:10], "little"),
                "trigger": classify_trigger(row[10]),
                "developer_note": note,
            }
        )
    return laps


def alignment_valid(rows: list[dict[str, Any]]) -> bool:
    return all(
        row["start_time"] % 60 == 0
        and row["distance_m"] % 10 == 0
        and row["end_time"] > row["start_time"]
        for row in rows
    )


def digest(rows: list[dict[str, Any]]) -> str:
    acc = 1469598103934665603
    for row in rows:
        acc ^= row["start_time"]
        acc = (acc * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        acc ^= row["end_time"]
        acc = (acc * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        acc ^= row["original_index"]
        acc = (acc * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"{acc:016x}"


def expected_stage(path: Path, stem: str) -> dict[str, Any]:
    rows = sorted(parse_fit(path), key=lambda row: row["start_time"])
    return {
        "source": str(path),
        "stem": stem,
        "staging_version": 1,
        "laps": rows,
        "digest": digest(rows),
    }


def expected_export(path: Path, stem: str) -> dict[str, Any]:
    stage = expected_stage(path, stem)
    return {
        "schema": "fit-lap-export/1",
        "source": stage["source"],
        "stem": stage["stem"],
        "staging_version": 1,
        "lap_count": len(stage["laps"]),
        "digest": stage["digest"],
        "laps": [
            {
                "lap_index": idx,
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "duration_s": row["end_time"] - row["start_time"],
                "distance_m": row["distance_m"],
                "trigger": row["trigger"],
                "developer_note": row["developer_note"],
            }
            for idx, row in enumerate(stage["laps"])
        ],
    }


def load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
