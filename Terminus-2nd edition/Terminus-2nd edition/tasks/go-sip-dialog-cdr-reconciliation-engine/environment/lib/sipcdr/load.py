"""Load SIP transcript JSONL for a scenario directory (BROKEN baseline)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_scenario(dir_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = Path(dir_path)
    pol = json.loads((root / "policy.json").read_text(encoding="utf-8"))
    paths = list(root.glob("*.siplog"))
    msgs: list[dict[str, Any]] = []
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                msgs.append(json.loads(line))
    return msgs, pol
