"""Load duel admit-log JSONL for a scenario directory (GOLDEN)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_scenario(dir_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = Path(dir_path)
    pol = json.loads((root / "policy.json").read_text(encoding="utf-8"))
    paths = sorted(root.glob("*.duellog"))
    msgs: list[dict[str, Any]] = []
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                msgs.append(json.loads(line))
    msgs.sort(key=lambda r: (int(r.get("ts_ms") or 0), int(r.get("cseq") or 0)))
    return msgs, pol
