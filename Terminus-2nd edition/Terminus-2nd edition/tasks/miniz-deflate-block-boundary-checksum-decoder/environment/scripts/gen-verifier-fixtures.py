#!/usr/bin/env python3
"""Build hidden zlib streams under /opt/verifier-fixtures/streams for TB3 traps."""

from __future__ import annotations

import os
import pathlib
import struct
import zlib

OUT = pathlib.Path("/opt/verifier-fixtures/streams")
OUT.mkdir(parents=True, exist_ok=True)

TB3_SEED = int(os.environ.get("TB3_BLOCK_SEED", "29"))


class BitWriter:
    def __init__(self) -> None:
        self.data = bytearray()
        self.acc = 0
        self.nbits = 0

    def write_bits(self, value: int, count: int) -> None:
        self.acc |= (value & ((1 << count) - 1)) << self.nbits
        self.nbits += count
        while self.nbits >= 8:
            self.data.append(self.acc & 0xFF)
            self.acc >>= 8
            self.nbits -= 8

    def align(self) -> None:
        if self.nbits:
            self.data.append(self.acc & 0xFF)
            self.acc = 0
            self.nbits = 0


def deflate_stored_chunks(chunks: list[bytes]) -> bytes:
    bw = BitWriter()
    for idx, chunk in enumerate(chunks):
        final = 1 if idx == len(chunks) - 1 else 0
        bw.write_bits(final, 1)
        bw.write_bits(0, 2)
        bw.align()
        ln = len(chunk)
        bw.data.extend(struct.pack("<HH", ln, 0xFFFF ^ ln))
        bw.data.extend(chunk)
    return bytes(bw.data)


def make_zlib(payload: bytes, name: str, chunks: list[bytes] | None = None) -> None:
    raw = deflate_stored_chunks(chunks or [payload])
    adler = zlib.adler32(payload) & 0xFFFFFFFF
    cmf, flg = 0x78, 0x01
    while ((cmf << 8) + flg) % 31:
        flg += 1
    blob = bytes([cmf, flg]) + raw + struct.pack(">I", adler)
    (OUT / f"{name}.zlib").write_bytes(blob)


part_a = bytes([(TB3_SEED + i) % 256 for i in range(120)])
part_b = bytes([(TB3_SEED * 3 + i) % 256 for i in range(180)])
make_zlib(part_a + part_b, "tb3_chain", chunks=[part_a, b"", part_b])

head = bytes([(TB3_SEED + 7 + i) % 256 for i in range(64)])
tail = head + (b"LZ" * 4096) + head
(OUT / "tb3_lz77.zlib").write_bytes(zlib.compress(tail, level=6))

print(f"generated {len(list(OUT.glob('*.zlib')))} verifier streams under {OUT}")
