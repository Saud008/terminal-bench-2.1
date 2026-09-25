#!/usr/bin/env python3
"""Generate SRCDEM fixtures for demo-index (image build only)."""

from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fixtures" / "demos"
MAGIC = b"SRCDEM"
HEADER_SIZE = 36
PKT_USERCMD = 0x01
PKT_SIGNON = 0x02
PKT_STRING = 0x03


def pack_header(
    *,
    flags: int,
    signon_tick_base: int,
    tick_count: int,
    str_count: int,
    packet_stream_len: int,
    str_index_off: int,
    tick_index_off: int,
    packet_off: int,
) -> bytes:
    buf = bytearray(HEADER_SIZE)
    buf[0:6] = MAGIC
    buf[6] = 1
    buf[7] = flags
    struct.pack_into("<I", buf, 8, signon_tick_base)
    struct.pack_into("<HH", buf, 12, tick_count, str_count)
    struct.pack_into("<I", buf, 16, packet_stream_len)
    struct.pack_into("<III", buf, 20, str_index_off, tick_index_off, packet_off)
    return bytes(buf)


def build_strings(strings: list[str]) -> tuple[bytes, list[int]]:
    blob = b"\x00".join(s.encode("utf-8") for s in strings) + b"\x00"
    base = HEADER_SIZE + len(strings) * 4
    offsets: list[int] = []
    cursor = base
    for s in strings:
        offsets.append(cursor)
        cursor += len(s.encode("utf-8")) + 1
    return blob, offsets


def encode_packet(pkt: dict) -> bytes:
    kind = pkt["type"]
    if kind == "usercmd":
        return struct.pack("<BBHI", PKT_USERCMD, pkt["str_idx"], pkt["seq"], pkt["arg"])
    if kind == "signon":
        return struct.pack("<BI", PKT_SIGNON, pkt["new_base"])
    if kind == "string":
        return struct.pack("<BB", PKT_STRING, pkt["str_idx"])
    raise ValueError(f"unknown packet {kind}")


def write_demo(path: Path, spec: dict) -> None:
    strings: list[str] = spec["strings"]
    ticks: list[dict] = spec["ticks"]
    flags = spec.get("flags", 0)
    signon_base = spec.get("signon_tick_base", 0)

    str_blob, str_offs = build_strings(strings)
    str_index_off = HEADER_SIZE
    str_data_off = HEADER_SIZE + len(strings) * 4

    stream = bytearray()
    tick_desc: list[dict] = []
    packet_idx = 0
    for tick in ticks:
        first = packet_idx
        count = 0
        for pkt in tick["packets"]:
            stream += encode_packet(pkt)
            packet_idx += 1
            count += 1
        tick_desc.append(
            {
                "rel_tick": tick["rel_tick"],
                "first_packet_idx": first,
                "packet_count": count,
                "storage_ord": tick.get("storage_ord", 0),
            }
        )

    packet_off = str_data_off + len(str_blob)
    packet_stream = bytes(stream)
    if spec.get("truncate_bytes", 0):
        packet_stream = packet_stream[: -int(spec["truncate_bytes"])]

    tick_index_off = packet_off + len(packet_stream)
    body = bytearray()
    body += pack_header(
        flags=flags,
        signon_tick_base=signon_base,
        tick_count=len(tick_desc),
        str_count=len(strings),
        packet_stream_len=len(packet_stream),
        str_index_off=str_index_off,
        tick_index_off=tick_index_off,
        packet_off=packet_off,
    )
    for off in str_offs:
        body += struct.pack("<I", off)
    body += str_blob
    body += packet_stream
    for td in tick_desc:
        body += struct.pack(
            "<IIHHI",
            td["rel_tick"],
            td["first_packet_idx"],
            td["packet_count"],
            td["storage_ord"],
            0,
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def main() -> None:
    demos = {
        "alpha/late.dem": {
            "signon_tick_base": 100,
            "strings": ["move_fwd", "jump"],
            "ticks": [
                {
                    "rel_tick": 0,
                    "packets": [{"type": "usercmd", "str_idx": 0, "seq": 1, "arg": 10}],
                },
                {
                    "rel_tick": 2,
                    "packets": [{"type": "usercmd", "str_idx": 1, "seq": 2, "arg": 20}],
                },
            ],
        },
        "beta/early.dem": {
            "signon_tick_base": 200,
            "strings": ["beta_cmd"],
            "ticks": [
                {
                    "rel_tick": 0,
                    "packets": [{"type": "usercmd", "str_idx": 0, "seq": 1, "arg": 5}],
                },
            ],
        },
        "signon/reset.dem": {
            "signon_tick_base": 50,
            "strings": ["pre_reset", "post_reset"],
            "ticks": [
                {
                    "rel_tick": 0,
                    "packets": [{"type": "usercmd", "str_idx": 0, "seq": 1, "arg": 1}],
                },
                {
                    "rel_tick": 1,
                    "packets": [
                        {"type": "signon", "new_base": 1000},
                        {"type": "usercmd", "str_idx": 1, "seq": 2, "arg": 2},
                    ],
                },
                {
                    "rel_tick": 3,
                    "packets": [{"type": "usercmd", "str_idx": 1, "seq": 3, "arg": 3}],
                },
            ],
        },
        "strings/highidx.dem": {
            "signon_tick_base": 0,
            "strings": [f"str_{i}" for i in range(130)],
            "ticks": [
                {
                    "rel_tick": 0,
                    "packets": [
                        {"type": "string", "str_idx": 129},
                        {"type": "usercmd", "str_idx": 129, "seq": 1, "arg": 99},
                    ],
                },
            ],
        },
        "loop/session.dem": {
            "flags": 1,
            "signon_tick_base": 300,
            "strings": ["loop_action"],
            "ticks": [
                {
                    "rel_tick": 0,
                    "packets": [{"type": "usercmd", "str_idx": 0, "seq": 10, "arg": 7}],
                },
                {
                    "rel_tick": 1,
                    "packets": [{"type": "usercmd", "str_idx": 0, "seq": 11, "arg": 8}],
                },
            ],
        },
        "broken/trunc.dem": {
            "signon_tick_base": 0,
            "strings": ["trunc"],
            "ticks": [
                {
                    "rel_tick": 0,
                    "packets": [{"type": "usercmd", "str_idx": 0, "seq": 1, "arg": 1}],
                },
            ],
            "truncate_bytes": 5,
        },
    }

    for rel, spec in demos.items():
        write_demo(OUT / rel, spec)

    seeds = ["primary01", "alt_gamma", "alt_delta"]
    (ROOT / "fixtures" / "seeds.json").write_text(
        json.dumps(seeds, indent=2) + "\n", encoding="utf-8"
    )
    print(f"generated {len(demos)} demos under {OUT}")


if __name__ == "__main__":
    main()
