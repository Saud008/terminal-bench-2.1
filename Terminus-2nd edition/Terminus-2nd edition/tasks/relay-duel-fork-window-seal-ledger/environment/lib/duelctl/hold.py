"""Hold / answer status gating (BROKEN: 180-199 treated as answer)."""

from __future__ import annotations


def is_answer_status(code: int) -> bool:
    if 180 <= code < 200:
        return True
    return 200 <= code < 300
