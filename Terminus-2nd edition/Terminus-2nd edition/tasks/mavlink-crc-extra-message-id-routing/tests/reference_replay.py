"""Independent Python replay of mav-core golden decode/publish logic."""

from __future__ import annotations

import json
import sqlite3
import struct
from pathlib import Path
from typing import Any

STX_V2 = 0xFD
MSG_HEARTBEAT = 0
MSG_SYS_STATUS = 1
MSG_GPS_RAW_INT = 24
MSG_EVENT_LOG = 11000

CRC_EXTRA: dict[int, int] = {
    MSG_HEARTBEAT: 50,
    MSG_SYS_STATUS: 124,
    MSG_GPS_RAW_INT: 24,
    MSG_EVENT_LOG: 195,
}

MESSAGE_NAME: dict[int, str] = {
    MSG_HEARTBEAT: "HEARTBEAT",
    MSG_SYS_STATUS: "SYS_STATUS",
    MSG_GPS_RAW_INT: "GPS_RAW_INT",
    MSG_EVENT_LOG: "EVENT_LOG",
}

CHECKPOINT_SCHEMA = """
CREATE TABLE IF NOT EXISTS accepted_frames (
    seed TEXT NOT NULL,
    sysid INTEGER NOT NULL,
    compid INTEGER NOT NULL,
    msg_id INTEGER NOT NULL,
    seq INTEGER NOT NULL,
    name TEXT NOT NULL,
    payload BLOB NOT NULL,
    PRIMARY KEY (seed, sysid, compid, msg_id, seq)
);
"""


def fnv1a64(input_str: str) -> int:
    h = 0xCBF29CE484222325
    for b in input_str.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def crc_accumulate(data: int, crc: int) -> int:
    tmp = (data ^ (crc & 0xFF)) & 0xFF
    tmp ^= (tmp << 4) & 0xFF
    return ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF


def crc_v2(header_and_payload: bytes, crc_extra: int) -> int:
    crc = 0xFFFF
    for b in header_and_payload:
        crc = crc_accumulate(b, crc)
    crc = crc_accumulate(crc_extra, crc)
    return crc


def build_crc_input(frame: dict[str, Any]) -> bytes:
    out = bytearray()
    out.append(frame["header_len"])
    out.append(frame["incompat"])
    out.append(frame["compat"])
    out.append(frame["seq"])
    out.append(frame["sysid"])
    out.append(frame["compid"])
    msg_id = frame["msg_id"]
    # MAVLink v2 always includes all three little-endian msg_id bytes in the CRC.
    out.append(msg_id & 0xFF)
    out.append((msg_id >> 8) & 0xFF)
    out.append((msg_id >> 16) & 0xFF)
    out.extend(frame["payload"])
    return bytes(out)


def extract_frames(data: bytes) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    idx = 0
    while idx < len(data):
        if data[idx] != STX_V2:
            idx += 1
            continue
        if idx + 10 > len(data):
            break
        header_len = data[idx + 1]
        payload_len = header_len
        frame_len = 10 + payload_len + 2
        if idx + frame_len > len(data):
            raise ValueError("truncated frame")
        msg_id = (
            data[idx + 7]
            | (data[idx + 8] << 8)
            | (data[idx + 9] << 16)
        )
        payload_start = idx + 10
        payload_end = payload_start + payload_len
        payload = data[payload_start:payload_end]
        crc_wire = data[payload_end] | (data[payload_end + 1] << 8)
        out.append(
            {
                "offset": idx,
                "header_len": header_len,
                "incompat": data[idx + 2],
                "compat": data[idx + 3],
                "seq": data[idx + 4],
                "sysid": data[idx + 5],
                "compid": data[idx + 6],
                "msg_id": msg_id,
                "payload": payload,
                "crc_wire": crc_wire,
            }
        )
        idx += frame_len
    return out


def permute_frames(frames: list[dict[str, Any]], seed: str) -> None:
    order = list(range(len(frames)))
    order.sort(key=lambda i: fnv1a64(f"{seed}:{i}"))
    original = list(frames)
    for i, src in enumerate(order):
        frames[i] = original[src]


def validate_frames(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for frame in frames:
        extra = CRC_EXTRA.get(frame["msg_id"])
        if extra is None:
            continue
        computed = crc_v2(build_crc_input(frame), extra)
        if computed != frame["crc_wire"]:
            continue
        out.append(
            {
                "msg_id": frame["msg_id"],
                "name": MESSAGE_NAME.get(frame["msg_id"], "UNKNOWN"),
                "sysid": frame["sysid"],
                "compid": frame["compid"],
                "seq": frame["seq"],
                "payload": frame["payload"],
            }
        )
    return out


def session_filter(
    frames: list[dict[str, Any]], seeded: dict[tuple[int, int], int]
) -> tuple[list[dict[str, Any]], int, dict[tuple[int, int], int]]:
    last_seq = dict(seeded)
    out: list[dict[str, Any]] = []
    dropped = 0
    for frame in frames:
        key = (frame["sysid"], frame["compid"])
        last = last_seq.get(key)
        if last is not None:
            rollback = (last - frame["seq"]) & 0xFF
            if 1 <= rollback < 127:
                dropped += 1
                continue
        last_seq[key] = frame["seq"]
        out.append(frame)
    return out, dropped, last_seq


def seed_session_from_checkpoint(
    seeded: dict[tuple[int, int], int], frames: list[dict[str, Any]]
) -> None:
    for frame in frames:
        key = (frame["sysid"], frame["compid"])
        seeded[key] = max(seeded.get(key, frame["seq"]), frame["seq"])


def dedup_frames(
    frames: list[dict[str, Any]], seen: set[tuple[int, int, int, int]]
) -> tuple[list[dict[str, Any]], int]:
    out: list[dict[str, Any]] = []
    local_seen: set[tuple[int, int, int, int]] = set()
    deduped = 0
    for frame in frames:
        key = (frame["sysid"], frame["compid"], frame["msg_id"], frame["seq"])
        if key in seen or key in local_seen:
            deduped += 1
            continue
        local_seen.add(key)
        out.append(frame)
    return out, deduped


def _checkpoint_connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(CHECKPOINT_SCHEMA)
    return conn


def load_checkpoint(path: Path, seed: str) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    conn = _checkpoint_connect(path)
    try:
        rows = conn.execute(
            "SELECT sysid, compid, msg_id, seq, name, payload FROM accepted_frames "
            "WHERE seed = ? ORDER BY rowid",
            (seed,),
        ).fetchall()
    finally:
        conn.close()
    out: list[dict[str, Any]] = []
    for sysid, compid, msg_id, seq, name, payload in rows:
        out.append(
            {
                "sysid": sysid,
                "compid": compid,
                "msg_id": msg_id,
                "seq": seq,
                "name": name,
                "payload": payload,
            }
        )
    return out


def checkpoint_seen_keys(path: Path, seed: str) -> set[tuple[int, int, int, int]]:
    if not path.is_file():
        return set()
    conn = _checkpoint_connect(path)
    try:
        rows = conn.execute(
            "SELECT sysid, compid, msg_id, seq FROM accepted_frames WHERE seed = ?",
            (seed,),
        ).fetchall()
    finally:
        conn.close()
    return {(r[0], r[1], r[2], r[3]) for r in rows}


def append_checkpoint(path: Path, seed: str, frames: list[dict[str, Any]]) -> None:
    if not frames:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = _checkpoint_connect(path)
    try:
        for frame in frames:
            conn.execute(
                "INSERT OR IGNORE INTO accepted_frames "
                "(seed, sysid, compid, msg_id, seq, name, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    seed,
                    frame["sysid"],
                    frame["compid"],
                    frame["msg_id"],
                    frame["seq"],
                    frame["name"],
                    frame["payload"],
                ),
            )
        conn.commit()
    finally:
        conn.close()


def stringify_scalar(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))


def extract_fact_values(frame: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if frame["msg_id"] == MSG_GPS_RAW_INT:
        payload = frame["payload"]
        if len(payload) < 12:
            raise ValueError("gps payload too short")
        time_boot_ms = struct.unpack_from("<I", payload, 0)[0]
        lat = struct.unpack_from("<i", payload, 4)[0]
        lon = struct.unpack_from("<i", payload, 8)[0]
        out.append(("time_boot_ms", stringify_scalar(time_boot_ms)))
        out.append(("lat", stringify_scalar(lat)))
        out.append(("lon", stringify_scalar(lon)))
    elif frame["msg_id"] == MSG_EVENT_LOG:
        payload = frame["payload"]
        if len(payload) < 8:
            raise ValueError("event payload too short")
        timestamp_ms = struct.unpack_from("<I", payload, 0)[0]
        event_seq = struct.unpack_from("<H", payload, 4)[0]
        value = struct.unpack_from("<h", payload, 6)[0]
        out.append(("timestamp_ms", stringify_scalar(timestamp_ms)))
        out.append(("event_seq", stringify_scalar(event_seq)))
        out.append(("value", stringify_scalar(value)))
    return out


def compute_diff_rows(
    checkpoint_frames: list[dict[str, Any]], new_frames: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    baseline: dict[tuple[int, int, int, str], str] = {}
    for frame in checkpoint_frames:
        for fact_key, value in extract_fact_values(frame):
            baseline[(frame["sysid"], frame["compid"], frame["msg_id"], fact_key)] = value

    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, int, int, str]] = set()
    for frame in new_frames:
        for fact_key, new_value in extract_fact_values(frame):
            key = (frame["sysid"], frame["compid"], frame["msg_id"], fact_key)
            if key in seen:
                continue
            old_value = baseline.get(key)
            if old_value is not None and old_value != new_value:
                rows.append(
                    {
                        "sysid": frame["sysid"],
                        "compid": frame["compid"],
                        "msg_id": frame["msg_id"],
                        "fact_key": fact_key,
                        "old_value": old_value,
                        "new_value": new_value,
                    }
                )
                seen.add(key)
    rows.sort(
        key=lambda r: (r["sysid"], r["compid"], r["msg_id"], r["fact_key"])
    )
    return rows


def decode_gps(frame: dict[str, Any]) -> dict[str, Any]:
    payload = frame["payload"]
    if len(payload) < 12:
        raise ValueError("gps payload too short")
    time_boot_ms = struct.unpack_from("<I", payload, 0)[0]
    lat = struct.unpack_from("<i", payload, 4)[0]
    lon = struct.unpack_from("<i", payload, 8)[0]
    return {
        "sysid": frame["sysid"],
        "compid": frame["compid"],
        "seq": frame["seq"],
        "time_boot_ms": time_boot_ms,
        "lat": lat,
        "lon": lon,
    }


def decode_event(frame: dict[str, Any]) -> dict[str, Any]:
    payload = frame["payload"]
    if len(payload) < 8:
        raise ValueError("event payload too short")
    timestamp_ms = struct.unpack_from("<I", payload, 0)[0]
    event_seq = struct.unpack_from("<H", payload, 4)[0]
    value = struct.unpack_from("<h", payload, 6)[0]
    return {
        "sysid": frame["sysid"],
        "compid": frame["compid"],
        "frame_seq": frame["seq"],
        "timestamp_ms": timestamp_ms,
        "event_seq": event_seq,
        "value": value,
    }


def build_export(
    frames: list[dict[str, Any]],
    seed: str,
    checkpoint_frame_count: int,
    deduped_count: int,
    stale_seq_dropped: int,
    diff_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    routes: list[dict[str, Any]] = []
    gps_fixes: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    for frame in frames:
        match = next(
            (
                r
                for r in routes
                if r["sysid"] == frame["sysid"]
                and r["compid"] == frame["compid"]
                and r["msg_id"] == frame["msg_id"]
            ),
            None,
        )
        if match is None:
            routes.append(
                {
                    "sysid": frame["sysid"],
                    "compid": frame["compid"],
                    "msg_id": frame["msg_id"],
                    "name": frame["name"],
                    "count": 1,
                }
            )
        else:
            match["count"] += 1
        routes.sort(key=lambda r: (r["sysid"], r["compid"], r["msg_id"]))

        if frame["msg_id"] == MSG_GPS_RAW_INT:
            gps_fixes.append(decode_gps(frame))
        if frame["msg_id"] == MSG_EVENT_LOG:
            events.append(decode_event(frame))

    events.sort(key=lambda e: (e["timestamp_ms"], e["event_seq"], e["frame_seq"]))

    return {
        "seed": seed,
        "valid_frame_count": len(frames),
        "checkpoint_frame_count": checkpoint_frame_count,
        "deduped_count": deduped_count,
        "stale_seq_dropped": stale_seq_dropped,
        "changed_fact_count": len(diff_rows),
        "diff_rows": diff_rows,
        "routes": routes,
        "gps_fixes": gps_fixes,
        "events": events,
    }


def decode_pass(
    stream_path: Path,
    seed: str,
    checkpoint: Path | None,
    resume: bool,
) -> dict[str, Any]:
    data = stream_path.read_bytes()
    raw = extract_frames(data)
    permute_frames(raw, seed)
    validated = validate_frames(raw)

    checkpoint_frames: list[dict[str, Any]] = []
    if resume and checkpoint is not None:
        checkpoint_frames = load_checkpoint(checkpoint, seed)

    checkpoint_count = len(checkpoint_frames)
    seen = checkpoint_seen_keys(checkpoint, seed) if resume and checkpoint else set()

    session_state: dict[tuple[int, int], int] = {}
    if resume:
        seed_session_from_checkpoint(session_state, checkpoint_frames)
    sessioned, stale_dropped, _ = session_filter(validated, session_state)
    deduped_new, dup_count = dedup_frames(sessioned, seen)

    if checkpoint is not None:
        append_checkpoint(checkpoint, seed, deduped_new)

    diff_rows = (
        compute_diff_rows(checkpoint_frames, deduped_new) if resume else []
    )
    merged = list(checkpoint_frames) + list(deduped_new)
    return build_export(
        merged,
        seed,
        checkpoint_count,
        dup_count,
        stale_dropped,
        diff_rows,
    )


def reference_export(stream_path: Path, seed: str) -> dict[str, Any]:
    return decode_pass(stream_path, seed, checkpoint=None, resume=False)


def reference_two_pass(
    stream_a: Path,
    stream_b: Path,
    seed: str,
    checkpoint: Path,
) -> dict[str, Any]:
    if checkpoint.is_file():
        checkpoint.unlink()
    decode_pass(stream_a, seed, checkpoint, resume=False)
    return decode_pass(stream_b, seed, checkpoint, resume=True)


def reference_three_pass(
    stream_a: Path,
    stream_b: Path,
    stream_c: Path,
    seed: str,
    checkpoint: Path,
) -> dict[str, Any]:
    if checkpoint.is_file():
        checkpoint.unlink()
    decode_pass(stream_a, seed, checkpoint, resume=False)
    decode_pass(stream_b, seed, checkpoint, resume=True)
    return decode_pass(stream_c, seed, checkpoint, resume=True)
