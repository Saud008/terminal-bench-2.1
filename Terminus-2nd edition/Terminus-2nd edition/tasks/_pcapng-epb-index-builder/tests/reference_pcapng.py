#!/usr/bin/env python3
"""Independent PCAPng reference parser for verifier (walks blocks from raw bytes)."""

from __future__ import annotations

import json
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

BT_SHB = 0x0A0D0D0A
BT_IDB = 0x00000001
BT_EPB = 0x00000006
OPT_IF_NAME = 2
OPT_EPB_CRC = 0x0EBC
OPT_END = 0


def crc32_ieee(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


@dataclass
class PacketRow:
    interface_id: int
    ts_ns: int
    file_offset: int
    cap_len: int
    packet_len: int

    def to_index_line(self) -> dict:
        return {
            "cap_len": self.cap_len,
            "file_offset": self.file_offset,
            "interface_id": self.interface_id,
            "packet_len": self.packet_len,
            "ts_ns": self.ts_ns,
        }


def _parse_options(blob: bytes, start: int) -> tuple[dict[int, bytes], int]:
    opts: dict[int, bytes] = {}
    pos = start
    while pos + 4 <= len(blob):
        code, olen = struct.unpack_from("<HH", blob, pos)
        if code == OPT_END:
            return opts, pos + 4
        val = blob[pos + 4 : pos + 4 + olen]
        opts[code] = val
        opt_pad = (olen + 3) & ~3
        pos += 4 + opt_pad
    return opts, pos


def ingest_capture(path: Path, ts_offset: int = 0) -> tuple[list[PacketRow], list[str], int, int]:
    """Return accepted rows, iface names in order, crc_rejected, duplicate_rejected."""
    data = path.read_bytes()
    iface_names: list[str] = []
    accepted: list[PacketRow] = []
    seen_keys: set[str] = set()
    crc_rejected = 0
    duplicate_rejected = 0
    offset = 0

    while offset + 8 <= len(data):
        block_type, total_len = struct.unpack_from("<II", data, offset)
        if total_len < 12 or offset + total_len > len(data):
            raise ValueError(f"bad block at {offset}")
        body_len = total_len - 12
        body = data[offset + 8 : offset + 8 + body_len]
        tail = struct.unpack_from("<I", data, offset + total_len - 4)[0]
        if tail != total_len:
            raise ValueError(f"length mismatch at {offset}")

        if block_type == BT_IDB:
            opts, _ = _parse_options(body, 8)
            name = opts.get(OPT_IF_NAME, b"").decode("utf-8", errors="replace").rstrip("\x00")
            if not name:
                name = f"iface{len(iface_names)}"
            iface_names.append(name)

        elif block_type == BT_EPB:
            if len(body) < 20:
                raise ValueError("short epb")
            raw_iface, ts_hi, ts_lo, cap_len, pkt_len = struct.unpack_from("<IIIII", body, 0)
            if raw_iface >= len(iface_names):
                raise ValueError(f"unknown iface {raw_iface}")
            ts_ns = ((ts_hi << 32) | ts_lo) + ts_offset
            cap = cap_len
            padded = (cap + 3) & ~3
            core_end = 20 + padded
            if len(body) < core_end:
                raise ValueError("epb core truncated")
            core = body[0:core_end]
            opts, _ = _parse_options(body, core_end)
            crc_val = opts.get(OPT_EPB_CRC)
            if crc_val is not None:
                if len(crc_val) != 4:
                    crc_rejected += 1
                else:
                    expected = struct.unpack("<I", crc_val)[0]
                    if crc32_ieee(core) != expected:
                        crc_rejected += 1
                        offset += total_len
                        continue

            key = f"{raw_iface}:{ts_ns}:{offset}"
            if key in seen_keys:
                duplicate_rejected += 1
            else:
                seen_keys.add(key)
                accepted.append(
                    PacketRow(
                        interface_id=raw_iface,
                        ts_ns=ts_ns,
                        file_offset=offset,
                        cap_len=cap_len,
                        packet_len=pkt_len,
                    )
                )

        offset += total_len

    accepted.sort(key=lambda r: (r.file_offset, r.interface_id, r.ts_ns))
    return accepted, iface_names, crc_rejected, duplicate_rejected


def canonical_index_bytes(rows: list[PacketRow]) -> bytes:
    lines = [json.dumps(r.to_index_line(), sort_keys=True, separators=(",", ":")) for r in rows]
    return "\n".join(lines).encode("utf-8")


def build_export_summary(
    rows: list[PacketRow],
    iface_names: list[str],
    crc_rejected: int,
    duplicate_rejected: int,
    index_bytes: bytes,
) -> dict:
    import hashlib

    per_iface: dict[int, int] = {}
    unique_ts: set[int] = set()
    for row in rows:
        per_iface[row.interface_id] = per_iface.get(row.interface_id, 0) + 1
        unique_ts.add(row.ts_ns)

    interfaces = []
    for idx, name in enumerate(iface_names):
        interfaces.append(
            {
                "interface_id": idx,
                "if_name": name,
                "packet_count": per_iface.get(idx, 0),
            }
        )

    return {
        "packet_count": len(unique_ts),
        "interfaces": interfaces,
        "index_digest": hashlib.sha256(index_bytes).hexdigest(),
        "crc_rejected": crc_rejected,
        "duplicate_rejected": duplicate_rejected,
    }


def shift_capture_timestamps(src: Path, dst: Path, offset: int) -> None:
    """Rewrite EPB timestamps by adding offset and refresh epb_body_crc32 options."""
    data = bytearray(src.read_bytes())
    pos = 0
    while pos + 8 <= len(data):
        block_type, total_len = struct.unpack_from("<II", data, pos)
        if total_len < 12:
            break
        if block_type == BT_EPB:
            body_start = pos + 8
            body_len = total_len - 12
            body = bytearray(data[body_start : body_start + body_len])
            if len(body) >= 20:
                cap_len = struct.unpack_from("<I", body, 12)[0]
                padded = (cap_len + 3) & ~3
                core_end = 20 + padded
                if len(body) >= core_end:
                    ts_hi, ts_lo = struct.unpack_from("<II", body, 4)
                    ts_ns = (ts_hi << 32) | ts_lo
                    ts_ns += offset
                    struct.pack_into("<II", body, 4, (ts_ns >> 32) & 0xFFFFFFFF, ts_ns & 0xFFFFFFFF)
                    core = bytes(body[:core_end])
                    opt_pos = core_end
                    while opt_pos + 4 <= len(body):
                        code, olen = struct.unpack_from("<HH", body, opt_pos)
                        if code == OPT_END:
                            break
                        if code == OPT_EPB_CRC and olen == 4:
                            struct.pack_into("<I", body, opt_pos + 4, crc32_ieee(core))
                        opt_pad = (olen + 3) & ~3
                        opt_pos += 4 + opt_pad
                    data[body_start : body_start + body_len] = body
        pos += total_len
    dst.write_bytes(bytes(data))
