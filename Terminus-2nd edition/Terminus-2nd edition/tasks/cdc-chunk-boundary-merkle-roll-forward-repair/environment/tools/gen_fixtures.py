#!/usr/bin/env python3
"""Generate deterministic binary fixtures."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "binaries"


def fill(size: int, tag: str) -> bytes:
    out = bytearray(size)
    seed = hashlib.sha256(tag.encode()).digest()
    for i in range(size):
        out[i] = seed[i % len(seed)] ^ (i & 0xFF)
    return bytes(out)


def repeat_pattern(size: int) -> bytes:
    out = bytearray(size)
    for i in range(size):
        out[i] = 0x41 if (i // 17) % 2 == 0 else 0x42
    return bytes(out)


def sparse(size: int) -> bytes:
    out = bytearray(size)
    for i in range(size):
        out[i] = 0x00
    for i in range(0, size, 113):
        out[i] = 0x7F
    return bytes(out)


def boundary_ramp(size: int) -> bytes:
    out = bytearray(size)
    for i in range(size):
        out[i] = (i * 17 + (i >> 8)) & 0xFF
    return bytes(out)


def odd_leaf_ramp(size: int) -> bytes:
    out = bytearray(size)
    for i in range(size):
        out[i] = (i * 31 + (i >> 4)) & 0xFF
    return bytes(out)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    ROOT.joinpath("baseline.bin").write_bytes(fill(8192, "baseline"))
    ROOT.joinpath("repeat.bin").write_bytes(repeat_pattern(8192))
    ROOT.joinpath("sparse.bin").write_bytes(sparse(8192))
    ROOT.joinpath("resume.bin").write_bytes(fill(16384, "resume"))
    ROOT.joinpath("boundary.bin").write_bytes(boundary_ramp(12288))
    ROOT.joinpath("oddleaf.bin").write_bytes(odd_leaf_ramp(4300))
    print(f"wrote fixtures under {ROOT}")


if __name__ == "__main__":
    main()
