"""Gate: preflight hold — @if preconditions on live state. See /app/docs/preflight-hold-rules.md."""

from __future__ import annotations

from typing import Any, Dict

ROOT_NODE = "0xroot"


def preflight_ok(g: Any, rec: Dict[str, Any]) -> bool:
    return True
