"""Reference digest and CIDR helpers mirrored by pytest contract math."""

from __future__ import annotations

import hashlib
import ipaddress


def digest_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def networks_overlap(a: str, b: str) -> bool:
    return ipaddress.ip_network(a, strict=False).overlaps(
        ipaddress.ip_network(b, strict=False)
    )
