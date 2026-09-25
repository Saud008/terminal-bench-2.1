#!/usr/bin/env python3
"""Write contract WAL segment files and SQLite DB pairs for fixtures."""

from __future__ import annotations

import sqlite3
import struct
import sys
import zlib
from pathlib import Path


def _u32be(n: int) -> bytes:
    return struct.pack(">I", n & 0xFFFFFFFF)


def _crc32_chunk(data: bytes, seed: int) -> int:
    return zlib.crc32(data, seed) & 0xFFFFFFFF


def _frame_checksum(frame_hdr16: bytes, payload: bytes, salt1: int, salt2: int) -> tuple[int, int]:
    c0 = _crc32_chunk(frame_hdr16[0:8], salt1)
    c1 = _crc32_chunk(frame_hdr16[8:16], salt2 ^ c0)
    c0 = _crc32_chunk(payload, c1)
    c1 = _crc32_chunk(frame_hdr16, c0)
    return c0, c1


def write_segment_wal(wal: Path, *, page_size: int, salt1: int, salt2: int, page_nos: list[int]) -> None:
    header = bytearray(32)
    header[0:4] = _u32be(0x377F0682)
    header[4:8] = _u32be(3007000)
    header[8:12] = _u32be(page_size)
    header[12:16] = _u32be(0)
    header[16:20] = _u32be(salt1)
    header[20:24] = _u32be(salt2)
    header[24:28] = _u32be(0)
    header[28:32] = _u32be(0)
    body = bytearray(header)
    db_size = max(page_nos) if page_nos else 1
    for page_no in page_nos:
        frame_hdr = bytearray(24)
        frame_hdr[0:4] = _u32be(page_no)
        frame_hdr[4:8] = _u32be(db_size)
        frame_hdr[8:12] = _u32be(salt1)
        frame_hdr[12:16] = _u32be(salt2)
        payload = bytes([page_no & 0xFF]) * page_size
        c0, c1 = _frame_checksum(bytes(frame_hdr[0:16]), payload, salt1, salt2)
        frame_hdr[16:20] = _u32be(c0)
        frame_hdr[20:24] = _u32be(c1)
        body.extend(frame_hdr)
        body.extend(payload)
    wal.write_bytes(body)


def populate_db(db: Path, rows: list[tuple[str, int]]) -> None:
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE entries (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT NOT NULL, qty INTEGER NOT NULL)"
    )
    for sku, qty in rows:
        conn.execute("INSERT INTO entries (sku, qty) VALUES (?, ?)", (sku, qty))
    conn.commit()
    conn.close()


def build_pair(db: Path, rows: list[tuple[str, int]], *, salt1: int, salt2: int, page_nos: list[int]) -> None:
    db.parent.mkdir(parents=True, exist_ok=True)
    wal = Path(str(db) + "-wal")
    for p in (db, wal, Path(str(db) + "-shm")):
        if p.exists():
            p.unlink()
    populate_db(db, rows)
    write_segment_wal(wal, page_size=4096, salt1=salt1, salt2=salt2, page_nos=page_nos)
    snap = Path(str(db) + ".wal.snap")
    snap.write_bytes(wal.read_bytes())


def main() -> int:
    state = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/app/state/ledger.db")
    fixture_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/app/fixtures/seed")
    fixture_dir.mkdir(parents=True, exist_ok=True)

    base_rows = [("SEED-100", 4), ("SEED-200", 2)]
    build_pair(state, base_rows, salt1=0xA11CE001, salt2=0xBADA55E0, page_nos=[1, 2])
    build_pair(
        fixture_dir / "ledger.db",
        base_rows + [("INIT-A", 1), ("INIT-B", 3)],
        salt1=0xC0FFEE01,
        salt2=0xDEADBEEF,
        page_nos=[1, 2, 3],
    )
    wal = fixture_dir / "ledger.db-wal"
    print(f"seeded {state} and {fixture_dir} wal_bytes={wal.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
