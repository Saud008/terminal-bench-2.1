"""Independent SRCDEM reference per /app/docs/demo-format.md and index-schema.md."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Any

MAGIC = b"SRCDEM"
HDR = 36
PKT_USERCMD = 0x01
PKT_SIGNON = 0x02
PKT_STRING = 0x03

BUILD_FILES = (
    "alpha/late.dem",
    "beta/early.dem",
    "loop/session.dem",
    "signon/reset.dem",
    "strings/highidx.dem",
)
PROBE_TRUNC = "broken/trunc.dem"


def arg_mask(seed: str, source: str) -> int:
    h = hashlib.sha256(f"{seed}:{source}:arg".encode()).hexdigest()
    return int(h[:8], 16)


def read_header(data: bytes) -> dict[str, int]:
    if data[:6] != MAGIC or data[6] != 1:
        raise ValueError("bad demo header")
    flags = data[7]
    signon, tc, sc, plen, sio, tio, poff = struct.unpack_from("<IHHIIII", data, 8)
    return {
        "flags": flags,
        "signon_tick_base": signon,
        "tick_count": tc,
        "str_count": sc,
        "packet_len": plen,
        "str_index_off": sio,
        "tick_index_off": tio,
        "packet_off": poff,
    }


def read_strings(data: bytes, hdr: dict[str, int]) -> list[str]:
    out: list[str] = []
    for i in range(hdr["str_count"]):
        (off,) = struct.unpack_from("<I", data, hdr["str_index_off"] + i * 4)
        end = data.index(0, off)
        out.append(data[off:end].decode("utf-8"))
    return out


def decode_packets(blob: bytes) -> tuple[list[dict[str, Any]], int]:
    pos = 0
    packets: list[dict[str, Any]] = []
    signon_resets = 0
    while pos < len(blob):
        if pos >= len(blob):
            break
        typ = blob[pos]
        if typ == PKT_USERCMD:
            if pos + 8 > len(blob):
                raise EOFError("partial usercmd")
            str_idx = blob[pos + 1]
            seq = struct.unpack_from("<H", blob, pos + 2)[0]
            arg = struct.unpack_from("<I", blob, pos + 4)[0]
            packets.append({"type": "usercmd", "str_idx": str_idx, "seq": seq, "arg": arg})
            pos += 8
        elif typ == PKT_SIGNON:
            if pos + 5 > len(blob):
                raise EOFError("partial signon")
            base = struct.unpack_from("<I", blob, pos + 1)[0]
            packets.append({"type": "signon_reset", "new_base": base})
            signon_resets += 1
            pos += 5
        elif typ == PKT_STRING:
            if pos + 2 > len(blob):
                raise EOFError("partial string")
            packets.append({"type": "string_ref", "str_idx": blob[pos + 1]})
            pos += 2
        else:
            raise ValueError(f"unknown packet {typ:#x}")
    return packets, signon_resets


def read_tick_index(data: bytes, hdr: dict[str, int]) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    off = hdr["tick_index_off"]
    for _ in range(hdr["tick_count"]):
        rel, first_idx, count, storage, _ = struct.unpack_from("<IIHHI", data, off)
        rows.append(
            {
                "rel_tick": rel,
                "first_packet_idx": first_idx,
                "packet_count": count,
                "storage_ord": storage,
            }
        )
        off += 16
    return rows


def parse_file(demo_path: Path, rel_source: str, seed: str) -> tuple[list[dict[str, Any]], int]:
    data = demo_path.read_bytes()
    hdr = read_header(data)
    strings = read_strings(data, hdr)
    stream = data[hdr["packet_off"] : hdr["packet_off"] + hdr["packet_len"]]
    all_packets, _ = decode_packets(stream)
    ticks = read_tick_index(data, hdr)
    mask = arg_mask(seed, rel_source)

    tick_base = hdr["signon_tick_base"]
    signon_resets = 0
    seen: set[tuple[int, int, str]] = set()
    out_ticks: list[dict[str, Any]] = []

    passes = 2 if (hdr["flags"] & 1) else 1
    for _pass in range(passes):
        tick_base = hdr["signon_tick_base"]
        for tick in ticks:
            global_tick = tick_base + tick["rel_tick"]
            start = tick["first_packet_idx"]
            end = start + tick["packet_count"]
            for pkt in all_packets[start:end]:
                if pkt["type"] == "signon_reset":
                    tick_base = pkt["new_base"]
                    global_tick = tick_base + tick["rel_tick"]
                    signon_resets += 1
                    continue
                if pkt["type"] != "usercmd":
                    continue
                key = (global_tick, pkt["seq"], rel_source)
                if key in seen:
                    continue
                seen.add(key)
                str_idx = pkt["str_idx"] & 0xFF
                out_ticks.append(
                    {
                        "global_tick": global_tick,
                        "source": rel_source,
                        "usercmds": [
                            {
                                "seq": pkt["seq"],
                                "str_idx": str_idx,
                                "string": strings[str_idx],
                                "arg": pkt["arg"] ^ mask,
                            }
                        ],
                    }
                )

    merged: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in out_ticks:
        key = (row["global_tick"], row["source"])
        merged.setdefault(key, []).extend(row["usercmds"])

    final_rows = []
    for (gtick, source) in sorted(merged.keys()):
        cmds = sorted(merged[(gtick, source)], key=lambda c: c["seq"])
        final_rows.append({"global_tick": gtick, "source": source, "usercmds": cmds})
    return final_rows, signon_resets


def reference_build(root: Path, seed: str) -> dict[str, Any]:
    files = list(BUILD_FILES)
    all_ticks: list[dict[str, Any]] = []
    total_usercmds = 0
    total_signon = 0
    for rel in files:
        rows, signon = parse_file(root / rel, rel, seed)
        for row in rows:
            all_ticks.append(row)
            total_usercmds += len(row["usercmds"])
        total_signon += signon

    all_ticks.sort(key=lambda r: (r["global_tick"], r["source"]))
    return {
        "index_version": 1,
        "seed": seed,
        "files": files,
        "ticks": all_ticks,
        "stats": {
            "file_count": len(files),
            "tick_count": len(all_ticks),
            "usercmd_count": total_usercmds,
            "signon_resets": total_signon,
        },
    }


def probe_exit_code(demo_path: Path) -> int:
    data = demo_path.read_bytes()
    hdr = read_header(data)
    blob = data[hdr["packet_off"] : hdr["packet_off"] + hdr["packet_len"]]
    try:
        decode_packets(blob)
        return 0
    except EOFError:
        return 2
    except ValueError:
        return 1
