"""Stdlib parity helpers for WBLE parsing and IHSH digest checks."""
from __future__ import annotations

import hashlib
import struct
import urllib.parse


def exchange_count_le(raw: bytes, offset: int) -> int:
    """Return the little-endian exchange count at offset."""
    return struct.unpack_from("<I", raw, offset)[0]


def ihsh_digest(preimage: bytes) -> bytes:
    """SHA-256 digest used by IHSH integrity rows."""
    return hashlib.sha256(preimage).digest()


def decode_path_segment(segment: str) -> str:
    """Percent-decode a single URL path segment."""
    return urllib.parse.unquote(segment, errors="strict")
