"""Rush/calm score windows (BROKEN: exclusive end minute)."""

from __future__ import annotations

from typing import Any


def tier_for_answer(pol: dict[str, Any], answer_ts: int) -> str:
    minute = int((answer_ts // 60000) % 1440)
    for w in pol.get("windows") or []:
        if int(w["start_minute"]) <= minute < int(w["end_minute"]):
            return str(w["tier"])
    return "calm"


def score_matches(pol: dict[str, Any], matches: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for k, d in matches.items():
        c = dict(d)
        if c.get("answered"):
            c["score_band"] = tier_for_answer(pol, int(c.get("answer_ts_ms") or 0))
            end = int(c.get("end_ts_ms") or 0)
            ans = int(c.get("answer_ts_ms") or 0)
            if end > ans:
                c["duration_sec"] = (end - ans) / 1000.0
        out[k] = c
    return out
