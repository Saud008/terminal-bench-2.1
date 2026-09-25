"""Independent reference layout calculator for fbctl wire and ledger artifacts."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Any

GAP_MAGIC = b"GAPS"
MR2R_MAGIC = b"MR2R"
LEDGER_MAGIC = b"FBLE"


def read_u32_le(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def read_u16_le(buf: bytes, off: int) -> int:
    return struct.unpack_from("<H", buf, off)[0]


def read_i32_le(buf: bytes, off: int) -> int:
    return struct.unpack_from("<i", buf, off)[0]


def scan_gaps(wire: bytes) -> list[dict[str, int]]:
    gaps: list[dict[str, int]] = []
    i = 0
    while i + 8 <= len(wire):
        if wire[i : i + 4] == GAP_MAGIC:
            span_len = read_u32_le(wire, i + 4)
            total = 8 + span_len
            if i + total <= len(wire):
                gaps.append({"start": i, "length": total})
                i += total
                continue
        i += 1
    return gaps


def discover_roots(wire: bytes) -> list[dict[str, int]]:
    if len(wire) >= 12 and wire[-12:-8] == MR2R_MAGIC:
        secondary_u = read_u32_le(wire, len(wire) - 8)
        primary_u = read_u32_le(wire, len(wire) - 4)
        primary_off = len(wire) - 12 - primary_u
        secondary_off = len(wire) - 12 - secondary_u
        return [
            _root_from_table(wire, primary_off),
            _root_from_table(wire, secondary_off),
        ]
    root_u = read_u32_le(wire, len(wire) - 4)
    table_off = len(wire) - 4 - root_u
    return [_root_from_table(wire, table_off)]


def _root_from_table(wire: bytes, table_off: int) -> dict[str, int]:
    soffset = read_i32_le(wire, table_off)
    vtable_off = table_off + soffset
    header_len = read_u16_le(wire, vtable_off)
    obj_size = read_u16_le(wire, vtable_off + 2)
    slots = decode_vtable_slots(wire, vtable_off, header_len)
    return {
        "table_off": table_off,
        "vtable_off": vtable_off,
        "vtable_len": header_len,
        "object_size": obj_size,
        "slots": slots,
    }


def decode_vtable_slots(wire: bytes, vtable_off: int, vtable_len: int) -> list[int]:
    slot_bytes = max(0, vtable_len - 4)
    slot_count = slot_bytes // 2
    slots: list[int] = []
    off = vtable_off + 4
    for _ in range(slot_count):
        voff = read_u16_le(wire, off)
        slots.append(0 if voff == 0 else int(voff))
        off += 2
    return slots


def parse_ledger(path: Path) -> dict[str, Any]:
    buf = path.read_bytes()
    assert buf[:4] == LEDGER_MAGIC
    off = 4
    _version = read_u32_le(buf, off)
    off += 4
    ingest_seq = read_u32_le(buf, off)
    off += 4
    count = read_u32_le(buf, off)
    off += 4
    entries: list[dict[str, Any]] = []
    for _ in range(count):
        entry, off = _read_entry(buf, off)
        entries.append(entry)
    return {"ingest_seq": ingest_seq, "entries": entries}


def _read_entry(buf: bytes, off: int) -> tuple[dict[str, Any], int]:
    name_len = read_u32_le(buf, off)
    off += 4
    name = buf[off : off + name_len].decode("utf-8")
    off += name_len
    wire_len = read_u32_le(buf, off)
    off += 4
    wire = buf[off : off + wire_len]
    off += wire_len
    root_count = read_u32_le(buf, off)
    off += 4
    roots: list[dict[str, Any]] = []
    for _ in range(root_count):
        root, off = _read_root(buf, off)
        roots.append(root)
    gap_count = read_u32_le(buf, off)
    off += 4
    gaps: list[dict[str, int]] = []
    for _ in range(gap_count):
        start = read_u32_le(buf, off)
        off += 4
        length = read_u32_le(buf, off)
        off += 4
        gaps.append({"start": start, "length": length})
    return {"name": name, "wire": wire, "roots": roots, "gaps": gaps}, off


def _read_root(buf: bytes, off: int) -> tuple[dict[str, Any], int]:
    table_off = read_u32_le(buf, off)
    off += 4
    vtable_off = read_u32_le(buf, off)
    off += 4
    vtable_len = read_u16_le(buf, off)
    off += 2
    object_size = read_u16_le(buf, off)
    off += 2
    slot_count = read_u32_le(buf, off)
    off += 4
    slots = [read_u32_le(buf, off + 4 * i) for i in range(slot_count)]
    off += 4 * slot_count
    return {
        "table_off": table_off,
        "vtable_off": vtable_off,
        "vtable_len": vtable_len,
        "object_size": object_size,
        "slots": slots,
    }, off


def reference_relayout(wire: bytes) -> bytes:
    gaps = scan_gaps(wire)
    out = bytearray(wire)
    for gap in gaps:
        start = gap["start"]
        end = start + gap["length"]
        out[start:end] = wire[start:end]
    for root in discover_roots(wire):
        table_off = root["table_off"]
        vtable_off = root["vtable_off"]
        soffset = vtable_off - table_off
        struct.pack_into("<i", out, table_off, soffset)
    return bytes(out)


def reference_seal(wire: bytes) -> str:
    return hashlib.sha256(wire).hexdigest()


def reference_roots_for_wire(path: Path) -> list[dict[str, Any]]:
    return discover_roots(path.read_bytes())
