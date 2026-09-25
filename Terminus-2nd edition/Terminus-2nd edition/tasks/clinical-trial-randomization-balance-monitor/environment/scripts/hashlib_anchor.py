"""Hash primitive anchor for verifier reference parity."""

import hashlib


def digest_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
