"""Terminate precedence (GOLDEN: CANCEL if not answered; BYE ignored if canceled)."""

from __future__ import annotations

from typing import Any


def apply_terminate(d: dict[str, Any], m: dict[str, Any]) -> None:
    method = m.get("method") or ""
    if method == "CANCEL" and not d.get("answered"):
        d["end_ts_ms"] = int(m.get("ts_ms") or 0)
        d["disposition"] = "canceled"
        return
    if method == "BYE":
        if d.get("disposition") == "canceled":
            return
        d["end_ts_ms"] = int(m.get("ts_ms") or 0)
        if d.get("answered"):
            d["disposition"] = "completed"
