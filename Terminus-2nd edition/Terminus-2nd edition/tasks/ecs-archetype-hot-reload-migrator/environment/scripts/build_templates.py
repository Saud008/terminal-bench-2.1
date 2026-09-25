"""Build drifted ECS SQLite + chunk binaries + replay journal templates."""

from __future__ import annotations

import json
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path

APP = Path("/app")
TEMPLATES = APP / "data" / "templates"
CHUNK_MAGIC = 0x45435331
STRIDE_V1 = 12
STRIDE_V2 = 14


def pack_i32_be(value: int) -> bytes:
    return struct.pack(">i", value)


def pack_i16_be(value: int) -> bytes:
    return struct.pack(">h", value)


def entity_payload_v1(x: int, y: int, dx: int, dy: int) -> bytes:
    body = bytearray(STRIDE_V1)
    body[0:4] = pack_i32_be(x)
    body[4:8] = pack_i32_be(y)
    body[8:10] = pack_i16_be(dx)
    body[10:12] = pack_i16_be(dy)
    return bytes(body)


def entity_payload_v2(x: int, y: int, dx: int, dy: int, hp: int = 100) -> bytes:
    body = bytearray(STRIDE_V2)
    body[0:4] = pack_i32_be(x)
    body[4:8] = pack_i32_be(y)
    body[8:10] = pack_i16_be(dx)
    body[10:12] = pack_i16_be(dy)
    body[12:14] = struct.pack(">H", hp)
    return bytes(body)


def encode_chunk(
    chunk_id: int,
    layout_version: int,
    entities: list[tuple[int, bytes]],
    *,
    stride: int,
) -> bytes:
    payload = bytearray()
    for stable_id, body in entities:
        payload.extend(struct.pack(">I", stable_id))
        padded = bytearray(body)
        padded.extend(b"\x00" * max(0, stride - len(padded)))
        payload.extend(padded[:stride])
    header = struct.pack(">IIII", CHUNK_MAGIC, chunk_id, layout_version, len(payload))
    return header + bytes(payload)


def write_db(path: Path) -> None:
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE entities (
              stable_id INTEGER PRIMARY KEY,
              archetype_id INTEGER NOT NULL,
              chunk_id INTEGER NOT NULL,
              slot INTEGER NOT NULL,
              alive INTEGER NOT NULL
            );
            CREATE TABLE archetypes (
              archetype_id INTEGER PRIMARY KEY,
              signature TEXT NOT NULL,
              entity_count INTEGER NOT NULL
            );
            CREATE TABLE tombstones (
              stable_id INTEGER PRIMARY KEY,
              tombstoned_at TEXT NOT NULL
            );
            CREATE TABLE migration_state (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              layout_version INTEGER NOT NULL,
              journal_status TEXT NOT NULL,
              commit_cursor INTEGER NOT NULL
            );
            """
        )
        rows = [
            (1, 1, 1, 0, 1),
            (2, 1, 1, 1, 1),
            (3, 2, 2, 0, 1),
            (4, 2, 2, 1, 1),
            (5, 1, 1, 2, 1),
            (0, 3, 2, 2, 1),
        ]
        conn.executemany(
            "INSERT INTO entities (stable_id, archetype_id, chunk_id, slot, alive) VALUES (?,?,?,?,?)",
            rows,
        )
        conn.execute(
            "INSERT INTO archetypes (archetype_id, signature, entity_count) VALUES (1,'Position+Velocity',3)"
        )
        conn.execute(
            "INSERT INTO archetypes (archetype_id, signature, entity_count) VALUES (2,'Position+Velocity',2)"
        )
        conn.execute(
            "INSERT INTO archetypes (archetype_id, signature, entity_count) VALUES (3,'Position+Velocity',1)"
        )
        conn.execute(
            "INSERT INTO tombstones (stable_id, tombstoned_at) VALUES (42, ?)",
            (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),),
        )
        conn.execute(
            "INSERT INTO migration_state (id, layout_version, journal_status, commit_cursor) VALUES (1,1,'pending',1)"
        )
        conn.commit()
    finally:
        conn.close()


def write_chunks(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    # Step 1 (add Health) already committed per journal; chunks carry v2 payloads.
    chunk1 = [
        (1, entity_payload_v2(10, 20, 1, 0)),
        (2, entity_payload_v2(30, 40, 0, 1)),
        (5, entity_payload_v2(50, 60, 2, 2)),
    ]
    chunk2 = [
        (3, entity_payload_v2(70, 80, -1, 1)),
        (4, entity_payload_v2(90, 100, 1, -1)),
        (0, entity_payload_v2(0, 0, 0, 0)),
    ]
    (dir_path / "chunk_0001.bin").write_bytes(
        encode_chunk(1, 2, chunk1, stride=STRIDE_V2)
    )
    (dir_path / "chunk_0002.bin").write_bytes(
        encode_chunk(2, 2, chunk2, stride=STRIDE_V2)
    )


def write_journal(path: Path) -> None:
    doc = {
        "status": "pending",
        "commit_cursor": 1,
        "entries": [
            {"step_order": 1, "chunk_id": 1, "committed": True},
            {"step_order": 1, "chunk_id": 2, "committed": True},
            {"step_order": 2, "chunk_id": 2, "committed": False},
        ],
    }
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    write_db(TEMPLATES / "hot_reload_alpha.db")
    write_chunks(TEMPLATES / "hot_reload_alpha_chunks")
    write_journal(TEMPLATES / "hot_reload_alpha.journal.json")
    print("wrote hot_reload_alpha templates")


if __name__ == "__main__":
    main()
