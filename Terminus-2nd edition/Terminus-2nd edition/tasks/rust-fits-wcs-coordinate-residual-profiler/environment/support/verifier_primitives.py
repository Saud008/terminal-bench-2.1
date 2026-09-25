"""Verifier-side primitives mirrored in pytest (see /app/docs/pytest-verifier-primitives.md)."""

from __future__ import annotations

import hashlib
import math


def sep_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r = math.pi / 180.0
    a1, d1, a2, d2 = ra1 * r, dec1 * r, ra2 * r, dec2 * r
    cos_d = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(a1 - a2)
    cos_d = max(-1.0, min(1.0, cos_d))
    return math.degrees(math.acos(cos_d)) * 3600.0


def sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
