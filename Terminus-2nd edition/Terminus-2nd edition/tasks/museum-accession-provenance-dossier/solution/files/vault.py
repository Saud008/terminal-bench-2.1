from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from musdoss import catalog


def write_vault_snapshot(path: str, seed: str, archive: str, arch: dict[str, Any]) -> None:
    if arch["archive_name"] != archive:
        raise ValueError(
            f'archive name mismatch: selected "{archive}", document names "{arch["archive_name"]}"'
        )
    prev = 0
    snap_path = Path(path)
    if snap_path.is_file():
        old = json.loads(snap_path.read_text(encoding="utf-8"))
        prev = int(old.get("archive_seq", 0))
    snap = catalog.materialize(arch, seed)
    snap["archive_seq"] = prev + 1
    snap["archive"] = archive
    _write_json(path, snap)


def read_vault_snapshot(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def snapshot_digest(path: str) -> str:
    raw = Path(path).read_bytes()
    return hashlib.sha256(raw).hexdigest()


def validate_seed_archive(snap: dict[str, Any], seed: str, archive: str) -> None:
    if snap.get("seed") != seed or snap.get("archive") != archive:
        raise ValueError("vault seed/archive mismatch")


def _write_json(path: str, value: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
