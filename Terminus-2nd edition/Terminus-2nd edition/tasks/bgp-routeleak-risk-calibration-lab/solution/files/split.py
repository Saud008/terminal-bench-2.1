"""Group-aware holdout split."""
from __future__ import annotations

from typing import Any


def assign_splits(examples: list[dict[str, Any]]) -> list[str]:
    groups = sorted({ex["peer_group"] for ex in examples})
    role_by_group: dict[str, str] = {}
    for i, g in enumerate(groups):
        r = i % 3
        role_by_group[g] = "train" if r == 0 else "validation" if r == 1 else "test"
    return [role_by_group[ex["peer_group"]] for ex in examples]
