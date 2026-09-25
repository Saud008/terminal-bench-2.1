"""Call-leg branch key (BROKEN: Call-ID|From-tag only)."""

from __future__ import annotations

from typing import Any


def branch_key(m: dict[str, Any]) -> str:
    return f"{m.get('call_id', '')}|{m.get('from_tag', '')}"
