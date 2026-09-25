#!/usr/bin/env python3
"""Generate hidden PCAPng fixtures for verifier-only tests."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

BT_SHB = 0x0A0D0D0A
BT_IDB = 0x00000001
BT_EPB = 0x00000006
OPT_IF_NAME = 2
OPT_EPB_CRC = 0x0EBC
OPT_END = 0


def _crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def _pad4(data: bytes) -> bytes:
    rem = len(data) % 4
    return data + b"\x00" * ((4 - rem) % 4)


def _option(code: int, value: bytes) -> bytes:
    return _pad4(struct.pack("<HH", code, len(value)) + value)


def _block(block_type: int, body: bytes) -> bytes:
    body = _pad4(body)
    total = 12 + len(body)
    return struct.pack("<II", block_type, total) + body + struct.pack("<I", total)


def _shb() -> bytes:
    body = struct.pack("<IHHQ", 0x1A2B3C4D, 1, 0, 0xFFFFFFFFFFFFFFFF)
    body += _option(OPT_END, b"")
    return _block(BT_SHB, body)


def _idb(name: str) -> bytes:
    body = struct.pack("<HHI", 1, 0, 65535)
    body += _option(OPT_IF_NAME, name.encode() + b"\x00")
    body += _option(OPT_END, b"")
    return _block(BT_IDB, body)


def _epb(iface: int, ts_ns: int, payload: bytes, *, crc: bool = True) -> bytes:
    core = struct.pack(
        "<IIIII",
        iface,
        (ts_ns >> 32) & 0xFFFFFFFF,
        ts_ns & 0xFFFFFFFF,
        len(payload),
        len(payload),
    )
    core += _pad4(payload)
    opts = b""
    if crc:
        opts += _option(OPT_EPB_CRC, struct.pack("<I", _crc32(core)))
    opts += _option(OPT_END, b"")
    return _block(BT_EPB, core + opts)


def build_hidden_dual() -> bytes:
    out = _shb()
    out += _idb("uplink")
    out += _idb("downlink")
    out += _idb("mgmt")
    base = 50_000_000_000
    out += _epb(0, base, b"\xaa" * 18)
    out += _epb(1, base, b"\xbb" * 22)
    out += _epb(2, base + 5, b"\xcc" * 10)
    out += _epb(0, base + 5, b"\xdd" * 14)
    out += _epb(1, base + 10, b"\xee" * 12)
    return out


def main() -> None:
    hidden = Path(__file__).resolve().parent / "hidden"
    hidden.mkdir(parents=True, exist_ok=True)
    (hidden / "triple_iface.pcapng").write_bytes(build_hidden_dual())


if __name__ == "__main__":
    main()
