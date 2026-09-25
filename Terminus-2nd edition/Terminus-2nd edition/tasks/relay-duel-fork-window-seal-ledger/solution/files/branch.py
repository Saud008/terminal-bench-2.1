"""Lane branch key (GOLDEN: include fork-tag when present)."""

from __future__ import annotations

from typing import Any


def branch_key(m: dict[str, Any]) -> str:
    tag = m.get("fork_tag") or ""
    if not tag:
        return f"{m.get('duel_id', '')}|{m.get('lane_tag', '')}"
    return f"{m.get('duel_id', '')}|{m.get('lane_tag', '')}|{tag}"


def branch_keys_equal(a: str, b: str) -> bool:
    return a == b
