"""Reference fingerprint helper cited by docs for verifier parity."""
import hashlib


def sha256_hex16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]
