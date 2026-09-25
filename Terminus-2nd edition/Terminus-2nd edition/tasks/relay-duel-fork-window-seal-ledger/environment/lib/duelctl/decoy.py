"""Telemetry decoy — must stay off the admit/fold/seal path."""

from __future__ import annotations

import time


class Span:
    def __init__(self, name: str) -> None:
        self.name = name
        self.start = time.time()

    def elapsed_ms(self) -> int:
        return int((time.time() - self.start) * 1000)


def begin(name: str) -> Span:
    return Span(name)
