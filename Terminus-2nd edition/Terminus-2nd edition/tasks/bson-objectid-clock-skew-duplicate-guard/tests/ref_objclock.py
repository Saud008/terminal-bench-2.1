"""Independent WireId layout checks for verifier expectations."""

from __future__ import annotations

import struct


def fnv1a64(data: bytes) -> int:
    h = 0xCBF29CE484222325
    prime = 0x100000001B3
    for b in data:
        h ^= b
        h = (h * prime) & 0xFFFFFFFFFFFFFFFF
    return h


def machine_fingerprint(machine_id: str) -> bytes:
    h = fnv1a64(machine_id.encode())
    return bytes([(h >> 32) & 0xFF, (h >> 24) & 0xFF, (h >> 16) & 0xFF, (h >> 8) & 0xFF, h & 0xFF])


def parse_hex(hex_id: str) -> tuple[int, bytes, int]:
    raw = bytes.fromhex(hex_id)
    if len(raw) != 12:
        raise ValueError("object id must be 12 bytes")
    ts = struct.unpack(">I", raw[0:4])[0]
    machine = raw[4:9]
    counter = (raw[9] << 16) | (raw[10] << 8) | raw[11]
    return ts, machine, counter


def expect_burst(now_unix: int, machine_id: str, count: int) -> list[tuple[int, bytes, int]]:
    machine = machine_fingerprint(machine_id)
    return [(now_unix, machine, i) for i in range(count)]


def extract_wireid_from_bson(doc: bytes) -> str:
    # BSON element order is type byte, then e_name cstring (MongoDB / bsonspec).
    needle = b"\x07_id\x00"
    idx = doc.find(needle)
    if idx < 0:
        raise ValueError("missing _id wireid field")
    start = idx + len(needle)
    if start + 12 > len(doc):
        raise ValueError("truncated wireid")
    return doc[start : start + 12].hex()
