"""Verifier-side math helpers documented in pytest-verifier-primitives.md."""

from __future__ import annotations

import hashlib
import math


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def separation_arcsec(dra: float, ddec: float) -> float:
    return math.hypot(dra, ddec)
