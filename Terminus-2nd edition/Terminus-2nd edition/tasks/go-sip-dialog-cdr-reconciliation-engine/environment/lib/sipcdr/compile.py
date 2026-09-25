"""Dialog compile fold — INVITE/status/BYE/CANCEL over branch keys."""

from __future__ import annotations

from typing import Any

from sipcdr.branch import branch_key
from sipcdr.clock import apply_skew
from sipcdr.dedupe import dedupe_messages
from sipcdr.provisional import is_answer_status
from sipcdr.terminate import apply_terminate


def compile_dialogs(msgs: list[dict[str, Any]], pol: dict[str, Any]) -> dict[str, dict[str, Any]]:
    msgs = dedupe_messages(msgs)
    msgs = apply_skew(msgs, pol)
    dialogs: dict[str, dict[str, Any]] = {}
    for m in msgs:
        key = branch_key(m)
        d = dialogs.get(key)
        if d is None:
            d = {
                "call_id": m.get("call_id", ""),
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
        if method in ("BYE", "CANCEL"):
            apply_terminate(d, m)
        dialogs[key] = d
    return dialogs
