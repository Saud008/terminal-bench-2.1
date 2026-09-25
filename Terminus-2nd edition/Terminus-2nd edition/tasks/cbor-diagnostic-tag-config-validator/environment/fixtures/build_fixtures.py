#!/usr/bin/env python3
"""Build bundled CBOR config fixtures for cbor-audit (self-contained encoder)."""

from __future__ import annotations

import struct
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent


def encode_uint(value: int) -> bytes:
    if value <= 23:
        return bytes([value])
    if value <= 0xFF:
        return bytes([0x18, value])
    if value <= 0xFFFF:
        return bytes([0x19, (value >> 8) & 0xFF, value & 0xFF])
    if value <= 0xFFFFFFFF:
        return bytes(
            [
                0x1A,
                (value >> 24) & 0xFF,
                (value >> 16) & 0xFF,
                (value >> 8) & 0xFF,
                value & 0xFF,
            ]
        )
    return struct.pack(">BQ", 0x1B, value)


def encode_text(text: str) -> bytes:
    raw = text.encode("utf-8")
    if len(raw) <= 23:
        return bytes([0x60 + len(raw)]) + raw
    return bytes([0x78, len(raw)]) + raw


def encode_bytes(data: bytes) -> bytes:
    if len(data) <= 23:
        return bytes([0x40 + len(data)]) + data
    return bytes([0x58, len(data)]) + data


def encode_array(items: list[bytes]) -> bytes:
    if len(items) <= 23:
        head = bytes([0x80 + len(items)])
    else:
        head = bytes([0x98, len(items)])
    return head + b"".join(items)


def encode_map_pairs(pairs: list[tuple[bytes, bytes]]) -> bytes:
    if len(pairs) <= 23:
        head = bytes([0xA0 + len(pairs)])
    else:
        head = bytes([0xB8, len(pairs)])
    return head + b"".join(k + v for k, v in pairs)


def wrap_tag24(inner: bytes) -> bytes:
    return bytes([0xD8, 0x18]) + encode_bytes(inner)


def encode_bundle(
    *,
    bundle_id: str,
    tags: list[tuple[str, int]],
    policy: str,
    nonce: bytes,
    version: int = 1,
) -> bytes:
    tag_items = []
    for label, tag in tags:
        tag_items.append(
            encode_map_pairs(
                [
                    (encode_text("label"), encode_text(label)),
                    (encode_text("tag"), encode_uint(tag)),
                ]
            )
        )
    inner_env = encode_map_pairs(
        [
            (encode_text("policy"), encode_text(policy)),
            (encode_text("nonce"), encode_bytes(nonce)),
        ]
    )
    return encode_map_pairs(
        [
            (encode_text("version"), encode_uint(version)),
            (encode_text("bundle_id"), encode_text(bundle_id)),
            (encode_text("diagnostic_tags"), encode_array(tag_items)),
            (encode_text("envelope"), wrap_tag24(inner_env)),
        ]
    )


def main() -> None:
    alpha = encode_bundle(
        bundle_id="alpha-config-v1",
        tags=[
            ("self-describe-cbor", 55799),
            ("encoded-cbor-item", 24),
            ("profile-alpha", 222315),
        ],
        policy="policy-alpha-short",
        nonce=b"alpha-nonce-01",
    )
    (FIXTURES / "alpha.cbor").write_bytes(alpha)

    beta = encode_bundle(
        bundle_id="beta-tagged-long-v1",
        tags=[
            ("self-describe-cbor", 55799),
            ("encoded-cbor-item", 24),
            ("profile-beta", 222316),
        ],
        policy="policy-beta-long-v1-padding-to-force-tag24-length-prefix",
        nonce=b"beta-nonce-99",
    )
    (FIXTURES / "beta_tagged.cbor").write_bytes(beta)

    invalid = encode_bundle(
        bundle_id="invalid-empty-policy",
        tags=[("encoded-cbor-item", 24)],
        policy="",
        nonce=b"bad",
    )
    (FIXTURES / "invalid_empty_policy.cbor").write_bytes(invalid)
    print("wrote fixtures")


if __name__ == "__main__":
    main()
