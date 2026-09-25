"""Terminate precedence (BROKEN: RESIGN always completed)."""

from __future__ import annotations

from typing import Any


def apply_terminate(d: dict[str, Any], m: dict[str, Any]) -> None:
    method = m.get("method") or ""
    if method == "RESIGN":
        d["end_ts_ms"] = int(m.get("ts_ms") or 0)
        d["disposition"] = "completed"
        return
    if method == "FORFEIT":
        d["end_ts_ms"] = int(m.get("ts_ms") or 0)
        d["disposition"] = "forfeited"
