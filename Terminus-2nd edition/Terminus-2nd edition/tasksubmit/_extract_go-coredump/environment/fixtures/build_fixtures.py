#!/usr/bin/env python3
"""Build ELF fixture binaries and crash JSONL bundles."""
from __future__ import annotations

import json
import os
import hashlib
import struct
from pathlib import Path

ROOT = Path("/app/fixtures")
HIDDEN = os.environ.get("COREIDX_HIDDEN_ROOT")
if HIDDEN:
    ROOT = Path(HIDDEN)


def build_elf(path: Path, build_id: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    note_name = b"GNU\x00"
    note_desc = build_id
    namesz = len(note_name)
    descsz = len(note_desc)
    note_hdr = struct.pack("<III", namesz, descsz, 3)
    note_body = note_hdr + note_name + b"\x00" * ((4 - (namesz % 4)) % 4)
    note_body += note_desc + b"\x00" * ((4 - (descsz % 4)) % 4)
    note_off = 0x200
    e_ident = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 8
    elf_hdr = struct.pack(
        "<16sHHIQQQIHHHHHH",
        e_ident,
        2,
        0x3E,
        1,
        0x401000,
        64,
        0x300,
        0,
        64,
        56,
        1,
        64,
        3,
        2,
    )
    phdr = struct.pack("<IIQQQQQQ", 4, 4, note_off, 0x600000, 0x600000, len(note_body), len(note_body), 4)
    buf = bytearray(b"\x00" * 0x400)
    buf[0:64] = elf_hdr
    buf[64:120] = phdr
    buf[note_off : note_off + len(note_body)] = note_body
    path.write_bytes(bytes(buf))


def write_catalog(base: Path) -> None:
    app_bin = base / "binaries" / "app"
    dbg_bin = base / "binaries" / "app.debug"
    build_elf(app_bin, bytes.fromhex("a1b2c3d4e5f60718"))
    build_elf(dbg_bin, bytes.fromhex("a1b2c3d4e5f60718"))
    lib_bin = base / "binaries" / "libhelper.so"
    build_elf(lib_bin, bytes.fromhex("0102030405060708"))
    catalog = {
        "binaries": {
            str(app_bin): {
                "build_id": "A1B2C3D4E5F60718",
                "stripped": True,
                "debug_path": str(dbg_bin),
                "symbols": [
                    {"offset": 0x1000, "name": "main.main"},
                    {"offset": 0x1100, "name": "main.worker"},
                    {"offset": 0x1200, "name": "main.crash"},
                ],
            },
            str(dbg_bin): {
                "build_id": "A1B2C3D4E5F60718",
                "stripped": False,
                "symbols": [
                    {"offset": 0x1000, "name": "main.main"},
                    {"offset": 0x1100, "name": "main.worker"},
                    {"offset": 0x1200, "name": "main.crash"},
                ],
            },
            str(lib_bin): {
                "build_id": "0102030405060708",
                "stripped": False,
                "symbols": [
                    {"offset": 0x200, "name": "helper.init"},
                    {"offset": 0x300, "name": "helper.run"},
                ],
            },
        }
    }
    cat_dir = base / "catalog"
    cat_dir.mkdir(parents=True, exist_ok=True)
    (cat_dir / "build_index.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256((cat_dir / "build_index.json").read_bytes()).hexdigest()
    (cat_dir / "build_index.sha256").write_text(digest + "\n", encoding="utf-8")


def write_crashes(base: Path) -> None:
    app = str(base / "binaries" / "app")
    lib = str(base / "binaries" / "libhelper.so")
    rows = [
        {
            "crash_id": "c-alpha-001",
            "timestamp": "2026-03-01T10:00:00Z",
            "signal": 11,
            "pid": 1001,
            "threads": [{"name": "main", "frames": [{"pc": "0x401100", "module": "app"}]}],
            "mmap": [
                {"start": "0x400000", "end": "0x402000", "path": app, "file_offset": "0x0"},
            ],
        },
        {
            "crash_id": "c-alpha-002",
            "timestamp": "2026-03-01T10:05:00Z",
            "signal": 11,
            "pid": 1002,
            "threads": [{"name": "main", "frames": [{"pc": "0x401100", "module": "app"}]}],
            "mmap": [
                {"start": "0x400000", "end": "0x402000", "path": app, "file_offset": "0x0"},
            ],
        },
        {
            "crash_id": "c-bravo-lib",
            "timestamp": "2026-03-01T11:00:00Z",
            "signal": 6,
            "pid": 2001,
            "threads": [{"name": "worker", "frames": [{"pc": "0x700300", "module": "libhelper.so"}]}],
            "mmap": [
                {"start": "0x700000", "end": "0x701000", "path": lib, "file_offset": "0x0"},
                {"start": "0x700000", "end": "0x701000", "path": lib, "file_offset": "0x1000"},
            ],
        },
        {
            "crash_id": "c-charlie-edge",
            "timestamp": "2026-03-01T12:00:00Z",
            "signal": 11,
            "pid": 3001,
            "threads": [{"name": "main", "frames": [{"pc": "0x401200", "module": "app"}]}],
            "mmap": [
                {"start": "0x400000", "end": "0x401201", "path": app, "file_offset": "0x0"},
            ],
        },
    ]
    crash_dir = base / "crashes"
    crash_dir.mkdir(parents=True, exist_ok=True)
    (crash_dir / "bundle.crash.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )


def write_hidden_bundle(base: Path) -> None:
    svc = base / "binaries" / "svc"
    build_elf(svc, bytes.fromhex("deadbeef00000001"))
    catalog = {
        "binaries": {
            str(svc): {
                "build_id": "DEADBEEF00000001",
                "stripped": False,
                "symbols": [{"offset": 0x500, "name": "svc.handle"}],
            }
        }
    }
    cat_dir = base / "catalog"
    cat_dir.mkdir(parents=True, exist_ok=True)
    (cat_dir / "build_index.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256((cat_dir / "build_index.json").read_bytes()).hexdigest()
    (cat_dir / "build_index.sha256").write_text(digest + "\n", encoding="utf-8")
    crash = {
        "crash_id": "c-hidden-delta",
        "timestamp": "2026-04-01T08:00:00Z",
        "signal": 11,
        "pid": 9001,
        "threads": [{"name": "main", "frames": [{"pc": "0x400500", "module": "svc"}]}],
        "mmap": [{"start": "0x400000", "end": "0x401000", "path": str(svc), "file_offset": "0x0"}],
    }
    crash_dir = base / "crashes"
    crash_dir.mkdir(parents=True, exist_ok=True)
    (crash_dir / "hidden.crash.jsonl").write_text(json.dumps(crash) + "\n", encoding="utf-8")


def main() -> None:
    if HIDDEN:
        write_hidden_bundle(ROOT)
    else:
        write_catalog(ROOT)
        write_crashes(ROOT)
    print(f"fixtures built under {ROOT}")


if __name__ == "__main__":
    main()
