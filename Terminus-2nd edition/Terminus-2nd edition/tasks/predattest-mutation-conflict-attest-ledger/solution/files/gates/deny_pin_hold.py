"""Gate: deny-pin hold — policy hold on pinned attrs. See /app/docs/deny-pin-hold.md."""

from __future__ import annotations

from typing import List


def attr_is_held(attr: str, hold_attrs: List[str]) -> bool:
    return any(attr == pinned for pinned in hold_attrs)
