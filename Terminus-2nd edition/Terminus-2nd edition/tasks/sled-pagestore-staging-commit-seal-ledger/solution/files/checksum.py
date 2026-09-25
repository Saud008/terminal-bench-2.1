from __future__ import annotations


def page_checksum(header: dict, body: bytes) -> int:
    acc = 0xFFFFFFFF
    gen = int(header["generation"])
    for b in gen.to_bytes(8, "little"):
        acc = (acc * 16777619) ^ b
        acc &= 0xFFFFFFFF
    for b in body:
        acc = (acc * 16777619) ^ b
        acc &= 0xFFFFFFFF
    return acc
