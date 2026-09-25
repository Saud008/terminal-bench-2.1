"""Retransmit suppression (GOLDEN: branch|method|cseq|status)."""

from __future__ import annotations

from typing import Any

from sipcdr.branch import branch_key


def dedupe_messages(msgs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for m in msgs:
        method = m.get("method") or ""
        if not method:
            method = "status"
        sig = f"{branch_key(m)}|{method}|{int(m.get('cseq') or 0)}|{int(m.get('status') or 0)}"
        if sig in seen:
            continue
        seen.add(sig)
        out.append(m)
    return out
