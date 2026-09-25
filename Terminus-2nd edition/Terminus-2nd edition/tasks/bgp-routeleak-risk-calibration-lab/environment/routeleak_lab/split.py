"""Group-aware holdout split (broken baseline)."""
from __future__ import annotations

from typing import Any


def assign_splits(examples: list[dict[str, Any]]) -> list[str]:
    roles = []
    for i, _ex in enumerate(examples):
        # broken: per-example modulo ignores peer_group cohesion
        r = i % 3
        roles.append("train" if r == 0 else "validation" if r == 1 else "test")
    return roles
