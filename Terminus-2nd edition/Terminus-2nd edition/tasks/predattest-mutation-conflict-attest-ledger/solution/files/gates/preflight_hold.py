"""Gate: preflight hold — @if preconditions on live state. See /app/docs/preflight-hold-rules.md."""

from __future__ import annotations

from typing import Any, Dict

ROOT_NODE = "0xroot"


def preflight_ok(g: Any, rec: Dict[str, Any]) -> bool:
    for c in rec.get("preconds") or []:
        val, ok = g.get_scalar(ROOT_NODE, c["attr"])
        if not ok:
            return False
        if c.get("op") == "eq":
            if val != c["value"]:
                return False
        else:
            return False
    return True
