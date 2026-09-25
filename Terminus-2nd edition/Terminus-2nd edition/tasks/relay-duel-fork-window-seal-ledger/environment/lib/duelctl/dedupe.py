"""Retransmit suppression (BROKEN: identity / no dedupe)."""

from __future__ import annotations

from typing import Any


def dedupe_messages(msgs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return list(msgs)
