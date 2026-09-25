"""Env-side digest helpers mirrored by pytest contract math."""

import hashlib


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
