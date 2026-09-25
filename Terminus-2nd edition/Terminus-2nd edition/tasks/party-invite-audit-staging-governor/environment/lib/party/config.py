"""Configuration loading for the local operations desk."""

from __future__ import annotations

import json
from pathlib import Path

PATH = Path("/app/config/party.json")


def load(path: Path = PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clamp_max_members(value: int | None, configured: int) -> int:
    if not value or value < 1:
        return configured
    return value
