"""Atlas audit digest helper — mirrors publish-atlas-fields sha256 contract."""

from __future__ import annotations

import hashlib


def sha256_hex(body: str) -> str:
    return hashlib.sha256(body.encode()).hexdigest()
