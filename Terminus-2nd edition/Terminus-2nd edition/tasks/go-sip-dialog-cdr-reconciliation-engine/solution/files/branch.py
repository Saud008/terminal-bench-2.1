"""Call-leg branch key (GOLDEN: include To-tag when present)."""

from __future__ import annotations

from typing import Any


def branch_key(m: dict[str, Any]) -> str:
    tag = m.get("to_tag") or ""
    if not tag:
        return f"{m.get('call_id', '')}|{m.get('from_tag', '')}"
    return f"{m.get('call_id', '')}|{m.get('from_tag', '')}|{tag}"


def branch_keys_equal(a: str, b: str) -> bool:
    return a == b
