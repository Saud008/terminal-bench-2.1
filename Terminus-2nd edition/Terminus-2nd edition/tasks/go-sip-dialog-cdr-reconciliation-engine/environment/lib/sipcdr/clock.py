"""Clock skew application (BROKEN: no skew)."""

from __future__ import annotations

from typing import Any


def apply_skew(msgs: list[dict[str, Any]], pol: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(m) for m in msgs]
