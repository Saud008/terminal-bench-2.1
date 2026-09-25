"""Gate: list-coalesce — list entry distinctness. See /app/docs/list-coalesce-rules.md."""

from __future__ import annotations

from typing import Dict, List, Tuple


def coalesce_entry(
    existing: List[Dict[str, str]], add: Dict[str, str]
) -> Tuple[List[Dict[str, str]], bool]:
    for e in existing:
        if e["value"] == add["value"] and e.get("lang", "") == add.get("lang", ""):
            return existing, False
    return existing + [add], True
