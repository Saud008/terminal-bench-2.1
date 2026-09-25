"""Decoy module — NOT wired into scan, compile, or publish.

An earlier rollout preview broke same-attr ties by the newest wall_time_ms
edit. The current conflict-precedence contract forbids consulting wall clocks
(see /app/docs/conflict-precedence-hold.md), so this helper is retained only
for historical reference and is never imported by the orchestrator or the
gate modules. Do not route precedence through it.
"""

from __future__ import annotations

from typing import Any, Dict, List


def newest_by_wall_time(pending: List[Dict[str, Any]]) -> Dict[Any, int]:
    winner: Dict[Any, int] = {}
    best_wall: Dict[Any, int] = {}
    for i, w in enumerate(pending):
        key = (w.get("uid"), w.get("attr"))
        wall = int(w.get("wall_time_ms", 0))
        if key not in best_wall or wall > best_wall[key]:
            best_wall[key] = wall
            winner[key] = i
    return winner
