"""Lock metadata validation helpers."""

from __future__ import annotations

import json
from pathlib import Path


def load_rows(workspace_root: Path) -> list[dict[str, str]]:
    data = json.loads((workspace_root / "lock-metadata.json").read_text(encoding="utf-8"))
    return list(data.get("packages", []))
