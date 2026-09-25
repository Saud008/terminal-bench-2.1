"""Build hidden verifier fixtures under /opt/verifier-fixtures/ecs-migrate/."""

from __future__ import annotations

import json
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/opt/verifier-fixtures/ecs-migrate")
LAYOUT = Path("/app/fixtures/layouts/hot_reload_alpha.json")
CHUNK_MAGIC = 0x45435331
STRIDE_V2 = 14


def pack_i32_be(value: int) -> bytes:
    return struct.pack(">i", value)


def pack_i16_be(value: int) -> bytes:
    return struct.pack(">h", value)


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
) -> bytes:
    payload = bytearray()
    for stable_id, body in entities:
        payload.extend(struct.pack(">I", stable_id))
        padded = bytearray(body)
        padded.extend(b"\x00" * max(0, STRIDE_V2 - len(padded)))
        payload.extend(padded[:STRIDE_V2])
    header = struct.pack(">IIII", CHUNK_MAGIC, chunk_id, layout_version, len(payload))
    return header + bytes(payload)


def write_tombstone_gap(case_dir: Path) -> None:
    db = case_dir / "ecs_meta.db"
    chunks = case_dir / "chunks"
    journal = case_dir / "replay.journal.json"
    chunks.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
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
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        for tid in (6, 7):
            conn.execute(
                "INSERT INTO tombstones (stable_id, tombstoned_at) VALUES (?, ?)",
                (tid, now),
            )
        conn.execute(
            "INSERT INTO migration_state (id, layout_version, journal_status, commit_cursor) VALUES (1,1,'pending',1)"
        )
        conn.commit()
    finally:
        conn.close()

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
    (chunks / "chunk_0001.bin").write_bytes(encode_chunk(1, 2, chunk1))
    (chunks / "chunk_0002.bin").write_bytes(encode_chunk(2, 2, chunk2))
    journal.write_text(
        json.dumps(
            {
                "status": "pending",
                "commit_cursor": 1,
                "entries": [
                    {"step_order": 1, "chunk_id": 1, "committed": True},
                    {"step_order": 1, "chunk_id": 2, "committed": True},
                    {"step_order": 2, "chunk_id": 2, "committed": False},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_health_only_archetype(case_dir: Path) -> None:
    db = case_dir / "ecs_meta.db"
    chunks = case_dir / "chunks"
    journal = case_dir / "replay.journal.json"
    chunks.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
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
            "INSERT INTO tombstones (stable_id, tombstoned_at) VALUES (42, ?)",
            (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),),
        )
        conn.execute(
            "INSERT INTO migration_state (id, layout_version, journal_status, commit_cursor) VALUES (1,1,'pending',1)"
        )
        conn.commit()
    finally:
        conn.close()

    health_only = bytearray(STRIDE_V2)
    health_only[12:14] = struct.pack(">H", 50)
    chunk1 = [
        (1, entity_payload_v2(10, 20, 1, 0)),
        (2, entity_payload_v2(30, 40, 0, 1)),
        (5, entity_payload_v2(50, 60, 2, 2)),
    ]
    chunk2 = [
        (3, entity_payload_v2(70, 80, -1, 1)),
        (4, entity_payload_v2(90, 100, 1, -1)),
        (0, bytes(health_only)),
    ]
    (chunks / "chunk_0001.bin").write_bytes(encode_chunk(1, 2, chunk1))
    (chunks / "chunk_0002.bin").write_bytes(encode_chunk(2, 2, chunk2))
    journal.write_text(
        json.dumps(
            {
                "status": "pending",
                "commit_cursor": 1,
                "entries": [
                    {"step_order": 1, "chunk_id": 1, "committed": True},
                    {"step_order": 1, "chunk_id": 2, "committed": True},
                    {"step_order": 2, "chunk_id": 2, "committed": False},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    gap = ROOT / "tombstone-gap"
    health = ROOT / "health-only-placeholder"
    write_tombstone_gap(gap)
    write_health_only_archetype(health)
    catalog = {
        "layout": str(LAYOUT),
        "cases": [
            {
                "id": "tombstone-gap",
                "db": str(gap / "ecs_meta.db"),
                "chunks": str(gap / "chunks"),
                "journal": str(gap / "replay.journal.json"),
                "expect_stable_id": 8,
            },
            {
                "id": "health-only-placeholder",
                "db": str(health / "ecs_meta.db"),
                "chunks": str(health / "chunks"),
                "journal": str(health / "replay.journal.json"),
                "expect_signature": "Health",
            },
        ],
    }
    (ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote verifier fixtures under {ROOT}")


if __name__ == "__main__":
    main()
