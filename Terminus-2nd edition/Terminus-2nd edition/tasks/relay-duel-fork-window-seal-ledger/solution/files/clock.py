"""Clock skew application (GOLDEN: add clock_skew_ms to every TsMS)."""

from __future__ import annotations

from typing import Any


def apply_skew(msgs: list[dict[str, Any]], pol: dict[str, Any]) -> list[dict[str, Any]]:
    skew = int(pol.get("clock_skew_ms") or 0)
    out: list[dict[str, Any]] = []
    for m in msgs:
        c = dict(m)
        c["ts_ms"] = int(c.get("ts_ms") or 0) + skew
        out.append(c)
    return out
