"""Match compile fold — CHALLENGE/status/RESIGN/FORFEIT over branch keys."""

from __future__ import annotations

from typing import Any

from duelctl.branch import branch_key
from duelctl.clock import apply_skew
from duelctl.dedupe import dedupe_messages
from duelctl.hold import is_answer_status
from duelctl.terminate import apply_terminate


def fold_branches(msgs: list[dict[str, Any]], pol: dict[str, Any]) -> dict[str, dict[str, Any]]:
    msgs = dedupe_messages(msgs)
    msgs = apply_skew(msgs, pol)
    matches: dict[str, dict[str, Any]] = {}
    for m in msgs:
        key = branch_key(m)
        d = matches.get(key)
        if d is None:
            d = {
                "duel_id": m.get("duel_id", ""),
                "branch_key": key,
                "answer_ts_ms": 0,
                "end_ts_ms": 0,
                "disposition": "",
                "answered": False,
            }
        status = int(m.get("status") or 0)
        if status > 0 and is_answer_status(status):
            d["answered"] = True
            if not d.get("answer_ts_ms"):
                d["answer_ts_ms"] = int(m.get("ts_ms") or 0)
        method = m.get("method") or ""
        if method in ("RESIGN", "FORFEIT"):
            apply_terminate(d, m)
        matches[key] = d
    return matches
