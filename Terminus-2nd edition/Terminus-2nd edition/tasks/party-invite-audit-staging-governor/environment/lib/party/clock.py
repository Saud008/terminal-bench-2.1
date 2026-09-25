"""Deterministic monotonic operation clock."""

from __future__ import annotations

import os


def mono_ms(value: int | None = None) -> int:
    if value is not None:
        return value
    raw = os.environ.get("PARTY_MONO_MS")
    if raw is None:
        raise ValueError("--mono-ms is required (or set PARTY_MONO_MS)")
    return int(raw)
