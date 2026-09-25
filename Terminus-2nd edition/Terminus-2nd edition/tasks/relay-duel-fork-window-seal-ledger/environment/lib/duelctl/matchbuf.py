"""Match-buffer staging I/O and seal digest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_PATH = "/app/state/match-buffer.json"


def write(path: str, st: dict[str, Any]) -> None:
    raw = json.dumps(st, indent=2) + "\n"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(raw, encoding="utf-8")


def read(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compute_seal(st: dict[str, Any]) -> str:
    """sha256 of canonical JSON over arena/scenario/matches (matches refmath)."""
    body = {
        "arena": st.get("arena", ""),
        "scenario": st.get("scenario", ""),
        "matches": st.get("matches") or {},
    }
    raw = json.dumps(body, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()
