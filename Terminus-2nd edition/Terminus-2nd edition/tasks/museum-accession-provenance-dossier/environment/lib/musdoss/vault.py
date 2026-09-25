from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from musdoss import catalog


def write_vault_snapshot(path: str, seed: str, archive: str, arch: dict[str, Any]) -> None:
    snap = catalog.materialize(arch, seed)
    snap["archive"] = archive
    _write_json(path, snap)


def read_vault_snapshot(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_seed_archive(snap: dict[str, Any], seed: str, archive: str) -> None:
    if snap.get("seed") != seed or snap.get("archive") != archive:
        raise ValueError("vault seed/archive mismatch")


def _write_json(path: str, value: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
