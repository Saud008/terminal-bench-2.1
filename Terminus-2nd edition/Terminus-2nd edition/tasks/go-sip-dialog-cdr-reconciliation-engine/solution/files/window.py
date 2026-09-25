"""Peak/offpeak billing windows (GOLDEN: inclusive end minute)."""

from __future__ import annotations

from typing import Any


def tier_for_answer(pol: dict[str, Any], answer_ts: int) -> str:
    minute = int((answer_ts // 60000) % 1440)
    for w in pol.get("windows") or []:
        if int(w["start_minute"]) <= minute <= int(w["end_minute"]):
            return str(w["tier"])
    return "offpeak"


def rate_dialogs(pol: dict[str, Any], dialogs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for k, d in dialogs.items():
        c = dict(d)
        if c.get("answered"):
            c["billing_tier"] = tier_for_answer(pol, int(c.get("answer_ts_ms") or 0))
            end = int(c.get("end_ts_ms") or 0)
            ans = int(c.get("answer_ts_ms") or 0)
            if end > ans:
                c["duration_sec"] = (end - ans) / 1000.0
        out[k] = c
    return out
