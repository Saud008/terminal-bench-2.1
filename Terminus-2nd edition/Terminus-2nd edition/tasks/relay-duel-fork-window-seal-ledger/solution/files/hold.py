"""Hold / answer status gating (GOLDEN)."""

from __future__ import annotations


def is_provision_status(code: int) -> bool:
    return code == 180 or code == 183


def is_answer_status(code: int) -> bool:
    if is_provision_status(code):
        return False
    return 200 <= code < 300


def mark_answered(code: int, answered: list[bool]) -> None:
    if is_answer_status(code):
        answered[0] = True
