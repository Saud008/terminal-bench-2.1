"""Gate: conflict-precedence hold — same node/attr precedence winner. See /app/docs/conflict-precedence-hold.md."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def resolve_precedence(pending: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, str], List[int]] = {}
    for i, w in enumerate(pending):
        if w["multi"]:
            continue
        groups.setdefault((w["uid"], w["attr"]), []).append(i)

    winner: Dict[Tuple[str, str], int] = {}
    for k, idxs in groups.items():
        winner[k] = idxs[0]

    out: List[Dict[str, Any]] = []
    for i, w in enumerate(pending):
        if w["multi"]:
            out.append({"edit": w, "reason": "list_coalesce", "winner": True})
            continue
        k = (w["uid"], w["attr"])
        if len(groups[k]) == 1:
            out.append({"edit": w, "reason": "commit_admit", "winner": True})
        elif winner[k] == i:
            out.append({"edit": w, "reason": "precedence_winner", "winner": True})
        else:
            out.append({"edit": w, "reason": "precedence_loser", "winner": False})
    return out
