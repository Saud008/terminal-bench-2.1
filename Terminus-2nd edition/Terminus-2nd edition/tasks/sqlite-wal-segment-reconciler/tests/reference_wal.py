#!/usr/bin/env python3
"""Independent WAL segment parser for verifier (not used by /app toolchain)."""

from __future__ import annotations

import shutil
import sqlite3
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WalHeader:
    page_size: int
    salt1: int
    salt2: int
    frame_count: int


def _u32be(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def _frame_checksum(frame_hdr16: bytes, payload: bytes, salt1: int, salt2: int) -> tuple[int, int]:
    c0 = zlib.crc32(frame_hdr16[0:8], salt1) & 0xFFFFFFFF
    c1 = zlib.crc32(frame_hdr16[8:16], (salt2 ^ c0) & 0xFFFFFFFF) & 0xFFFFFFFF
    c0 = zlib.crc32(payload, c1) & 0xFFFFFFFF
    c1 = zlib.crc32(frame_hdr16, c0) & 0xFFFFFFFF
    return c0, c1


def parse_wal_header(wal_path: Path) -> WalHeader:
    raw = wal_path.read_bytes()
    if len(raw) < 32:
        raise ValueError("wal too short")
    page_size = _u32be(raw, 8)
    salt1 = _u32be(raw, 16)
    salt2 = _u32be(raw, 20)
    if page_size <= 0:
        raise ValueError("invalid page size")
    frame_count = (len(raw) - 32) // (24 + page_size)
    return WalHeader(page_size=page_size, salt1=salt1, salt2=salt2, frame_count=frame_count)


def valid_frame_count(wal_path: Path) -> int:
    raw = wal_path.read_bytes()
    hdr = parse_wal_header(wal_path)
    psz = hdr.page_size
    valid = 0
    for fid in range(1, hdr.frame_count + 1):
        base = 32 + (fid - 1) * (24 + psz)
        frame = raw[base : base + 24 + psz]
        stored0 = _u32be(frame, 16)
        stored1 = _u32be(frame, 20)
        c0, c1 = _frame_checksum(frame[0:16], frame[24:], hdr.salt1, hdr.salt2)
        if c0 != stored0 or c1 != stored1:
            break
        valid += 1
    return valid


def make_wal_database(
    work_dir: Path,
    rows: list[tuple[str, int]],
    *,
    db_name: str = "ledger.db",
    salt1: int | None = None,
    salt2: int | None = None,
) -> Path:
    import secrets

    work_dir.mkdir(parents=True, exist_ok=True)
    db = work_dir / db_name
    for name in (f"{db.name}-wal", f"{db.name}-shm", f"{db.name}.wal.snap"):
        p = work_dir / name
        if p.exists():
            p.unlink()
    if db.exists():
        db.unlink()

    s1 = salt1 if salt1 is not None else secrets.randbits(32)
    s2 = salt2 if salt2 is not None else secrets.randbits(32)
    page_nos = list(range(1, len(rows) + 1))

    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE entries (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT NOT NULL, qty INTEGER NOT NULL)"
    )
    for sku, qty in rows:
        conn.execute("INSERT INTO entries (sku, qty) VALUES (?, ?)", (sku, qty))
    conn.commit()
    conn.close()

    sys_path = Path("/app/tools/build_seed_wal.py")
    if sys_path.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location("build_seed_wal", sys_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        mod.write_segment_wal(Path(str(db) + "-wal"), page_size=4096, salt1=s1, salt2=s2, page_nos=page_nos)
    wal = work_dir / f"{db_name}-wal"
    shutil.copy2(wal, work_dir / f"{db_name}.wal.snap")
    return db


def sqlite_scalar(db: Path, sql: str) -> int:
    conn = sqlite3.connect(db)
    try:
        row = conn.execute(sql).fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def distinct_applied_count(db: Path) -> int:
    return sqlite_scalar(db, "SELECT COUNT(DISTINCT frame_id) FROM _wal_applied")


def applied_count(db: Path) -> int:
    return sqlite_scalar(db, "SELECT COUNT(*) FROM _wal_applied")


def entry_count(db: Path) -> int:
    return sqlite_scalar(db, "SELECT COUNT(*) FROM entries")
