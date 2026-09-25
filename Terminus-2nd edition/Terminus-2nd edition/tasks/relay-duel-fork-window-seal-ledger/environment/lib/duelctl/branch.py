"""Lane branch key (BROKEN: duel_id|lane-tag only)."""

from __future__ import annotations

from typing import Any


def branch_key(m: dict[str, Any]) -> str:
    return f"{m.get('duel_id', '')}|{m.get('lane_tag', '')}"
