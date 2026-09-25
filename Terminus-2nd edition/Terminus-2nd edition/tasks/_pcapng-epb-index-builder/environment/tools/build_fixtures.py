#!/usr/bin/env python3
"""Build bundled PCAPng fixtures for the index builder image."""

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
    if rem:
        return data + b"\x00" * (4 - rem)
    return data


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


def _idb(if_name: str, link_type: int = 1) -> bytes:
    body = struct.pack("<HHI", link_type, 0, 65535)
    body += _option(OPT_IF_NAME, if_name.encode("utf-8") + b"\x00")
    body += _option(OPT_END, b"")
    return _block(BT_IDB, body)


def _epb(
    iface: int,
    ts_ns: int,
    payload: bytes,
    *,
    wire_len: int | None = None,
    crc: bool = True,
    bad_crc: bool = False,
) -> bytes:
    wire = wire_len if wire_len is not None else len(payload)
    core = struct.pack(
        "<IIIII",
        iface,
        (ts_ns >> 32) & 0xFFFFFFFF,
        ts_ns & 0xFFFFFFFF,
        len(payload),
        wire,
    )
    core += _pad4(payload)
    opts = b""
    if crc:
        val = _crc32(core)
        if bad_crc:
            val ^= 0xFFFFFFFF
        opts += _option(OPT_EPB_CRC, struct.pack("<I", val))
    opts += _option(OPT_END, b"")
    return _block(BT_EPB, core + opts)


def build_lan_capture() -> bytes:
    out = _shb()
    out += _idb("eth0")
    out += _epb(0, 1_000_000, b"\x00" * 14)
    out += _epb(0, 2_000_000, b"\xff" * 20)
    out += _epb(0, 3_000_000, b"\xaa\xbb\xcc")
    return out


def build_dual_iface() -> bytes:
    out = _shb()
    out += _idb("wan0")
    out += _idb("lan0")
    shared_ts = 9_999_000_000
    out += _epb(0, shared_ts, b"\x01" * 10)
    out += _epb(1, shared_ts, b"\x02" * 12)
    out += _epb(0, shared_ts + 1, b"\x03" * 8)
    out += _epb(1, shared_ts + 2, b"\x04" * 16)
    return out


def build_crc_trap() -> bytes:
    out = _shb()
    out += _idb("tap0")
    out += _epb(0, 100, b"\x11" * 6)
    out += _epb(0, 200, b"\x22" * 6, bad_crc=True)
    out += _epb(0, 300, b"\x33" * 6)
    return out


def main() -> None:
    root = Path(__file__).resolve().parent.parent / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    (root / "lan_single.pcapng").write_bytes(build_lan_capture())
    (root / "dual_iface.pcapng").write_bytes(build_dual_iface())
    (root / "crc_trap.pcapng").write_bytes(build_crc_trap())


if __name__ == "__main__":
    main()
