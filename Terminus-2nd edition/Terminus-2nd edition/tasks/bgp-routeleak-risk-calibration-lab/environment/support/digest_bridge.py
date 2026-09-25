"""Small helper package for verifier-visible digest plumbing."""
from __future__ import annotations

from tools.audit_digest_ref import sha256_hex


def digest_line(line: str) -> str:
    return sha256_hex(line)
