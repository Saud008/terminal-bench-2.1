from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PATH = Path("/app/state/membership-staging.json")


def write_staging(path: str | Path, st: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")


def read_staging(path: str | Path = DEFAULT_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
