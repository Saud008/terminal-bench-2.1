"""Snapshot and sealed model-card report (broken baseline)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def audit_digest(rows: list[dict[str, Any]]) -> str:
    # broken: re-sort by example_id before hashing
    ordered = sorted(rows, key=lambda r: r["example_id"])
    lines = [
        f"{r['example_id']}|{r['split']}|{r['label']}|{r['score']:.6f}|{r['predicted']}"
        for r in ordered
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def write_snapshot(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
