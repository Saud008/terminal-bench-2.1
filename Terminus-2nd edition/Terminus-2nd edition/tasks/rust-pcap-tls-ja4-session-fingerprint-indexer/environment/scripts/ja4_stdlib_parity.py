"""Stdlib parity helpers for JA4 capsule parsing and fingerprint hashing."""
from __future__ import annotations

import hashlib
import struct


def capsule_frame_count(raw: bytes) -> int:
    """Return the little-endian frame count from a CAPS capsule blob."""
    if raw[:4] != b"CAPS":
        raise ValueError("invalid capsule magic")
    return struct.unpack_from("<I", raw, 4)[0]


def extension_digest(extensions: list[int]) -> str:
    """Return the truncated SHA-256 hex digest used in JA4 extension hashing."""
    packed = b"".join(struct.pack(">H", code) for code in sorted(extensions))
    return hashlib.sha256(packed).hexdigest()[:12]
