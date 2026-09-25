"""Seed pool accessors for randomized rail scenario runs."""

from __future__ import annotations

import json
from pathlib import Path

APP = Path("/app")


def load_seed_pool() -> list[str]:
    data = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))
    return list(data["seeds"])
