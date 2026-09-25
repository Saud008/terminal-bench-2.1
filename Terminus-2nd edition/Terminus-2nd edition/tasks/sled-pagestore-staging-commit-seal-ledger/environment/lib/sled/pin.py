from __future__ import annotations

import json

from sled.config import PINS_DIR
from sled.registry import load_registry


def pin_snapshot(table: str, snapshot_id: str) -> None:
    reg = load_registry()
    pinned = [pid for pid in reg.get("pages", {}) if pid.startswith("root")]
    PINS_DIR.mkdir(parents=True, exist_ok=True)
    path = PINS_DIR / f"{table}-{snapshot_id}.json"
    path.write_text(
        json.dumps(
            {"table": table, "snapshot_id": snapshot_id, "pinned_pages": pinned},
            indent=2,
        ),
        encoding="utf-8",
    )


def load_pin_set(table: str) -> set[str]:
    pinned: set[str] = set()
    if not PINS_DIR.is_dir():
        return pinned
    for path in PINS_DIR.glob(f"{table}-*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        pinned.update(data.get("pinned_pages", []))
    return pinned
