"""Digest helpers mirroring package-normalization.md — env owns hashlib contract."""

from __future__ import annotations

import hashlib


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
