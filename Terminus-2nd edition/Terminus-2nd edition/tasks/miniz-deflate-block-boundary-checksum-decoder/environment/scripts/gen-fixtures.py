#!/usr/bin/env python3
"""Generate zlib fixtures using stored DEFLATE blocks (deterministic bit layout)."""

from __future__ import annotations

import pathlib
import struct
import zlib

OUT = pathlib.Path("/app/fixtures/streams")
OUT.mkdir(parents=True, exist_ok=True)


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


make_zlib(b"Hello deflate boundary repair", "hello")
make_zlib(bytes(range(256)), "bytes256")
make_zlib(b"abc", "tiny")
make_zlib(b"part-a" + b"part-b", "empty_mid", chunks=[b"part-a", b"", b"part-b"])
make_zlib(b"alpha-" + b"beta-" + b"gamma", "twopart", chunks=[b"alpha-", b"beta-", b"gamma"])

# Compressed DEFLATE blocks (fixed/dynamic Huffman + LZ77 backreferences)
def make_zlib_compress(payload: bytes, name: str, level: int = 6) -> None:
    (OUT / f"{name}.zlib").write_bytes(zlib.compress(payload, level=level))


def make_zlib_fixed(payload: bytes, name: str) -> None:
    compressor = zlib.compressobj(9, zlib.DEFLATED, 15, 8, zlib.Z_FIXED)
    (OUT / f"{name}.zlib").write_bytes(compressor.compress(payload) + compressor.flush())


pattern = (b"WIND" * 512) + (b"COPY" * 128)
make_zlib_compress(pattern, "window_repeat")
make_zlib_fixed((b"HUFF" * 2000) + bytes(range(32)), "huffman_bytes256")
make_zlib_compress(b"LZ77-" + (b"RING" * 9000), "lz77_ring")
make_zlib_compress(b"DYN" * 8000 + bytes(i % 256 for i in range(512)), "dynamic_tree")

print(f"generated {len(list(OUT.glob('*.zlib')))} streams")
