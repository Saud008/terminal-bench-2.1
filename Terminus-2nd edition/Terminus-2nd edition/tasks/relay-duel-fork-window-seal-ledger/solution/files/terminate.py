"""Terminate precedence (GOLDEN: FORFEIT if not answered; RESIGN ignored if forfeited)."""

from __future__ import annotations

from typing import Any


def apply_terminate(d: dict[str, Any], m: dict[str, Any]) -> None:
    method = m.get("method") or ""
    if method == "FORFEIT" and not d.get("answered"):
        d["end_ts_ms"] = int(m.get("ts_ms") or 0)
        d["disposition"] = "forfeited"
        return
    if method == "RESIGN":
        if d.get("disposition") == "forfeited":
            return
        d["end_ts_ms"] = int(m.get("ts_ms") or 0)
        if d.get("answered"):
            d["disposition"] = "completed"
