"""Validate prefix bundle JSON shape for lint helpers under /app/scripts/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_bundle(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
