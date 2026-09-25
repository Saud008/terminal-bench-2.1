"""Staging snapshot helpers for sheet seal audits."""

from __future__ import annotations

import json
import os
from pathlib import Path


def staging_snapshot_path() -> Path:
    root = Path(os.environ.get("SHEET_APP_ROOT", "/app"))
    return root / "output" / "sheet-staging-snapshot.json"


def staging_snapshot(seed: int, set_name: str, mark_count: int) -> dict:
    return {
        "stage": "sheet-staging",
        "seed": seed,
        "set": set_name,
        "mark_count": mark_count,
    }


def write_snapshot(seed: int, set_name: str, mark_count: int) -> Path:
    path = staging_snapshot_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = staging_snapshot(seed, set_name, mark_count)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
