"""Independent reference logic for blevectl ingest/export behavior."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

FNV_OFFSET = 14695981039346656037
FNV_PRIME = 1099511628211
U64_MASK = 0xFFFFFFFFFFFFFFFF


def fnv1_64(data: bytes) -> int:
    """Return the FNV-1 64-bit hash (multiply then xor) of data."""
    hashed = FNV_OFFSET
    for byte in data:
        hashed = (hashed * FNV_PRIME) & U64_MASK
        hashed ^= byte
    return hashed


def compute_checksum(doc_id: str, key: str, payload: str) -> int:
    """Return the segment admission checksum for a single record."""
    return fnv1_64(f"{doc_id}:{key}:{payload}".encode())


def load_records(batch_path: Path) -> list[dict]:
    """Parse a JSONL batch file into record dictionaries."""
    rows: list[dict] = []
    for raw in batch_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def validate_records(rows: list[dict]) -> bool:
    """Return True when every record checksum matches the FNV-1 contract."""
    return all(
        compute_checksum(row["id"], row["key"], row["payload"]) == int(row["checksum"])
        for row in rows
    )


def sort_keys(keys: list[str], collator_path: Path) -> list[str]:
    """Sort keys by collator rank, placing unlisted keys after listed keys."""
    cfg = json.loads(collator_path.read_text(encoding="utf-8"))
    rank = {key: index for index, key in enumerate(cfg["key_order"])}
    unlisted_rank = len(cfg["key_order"])
    return sorted(keys, key=lambda key: (rank.get(key, unlisted_rank), key))


def expected_export(batch_paths: list[Path], collator_path: Path) -> dict:
    """Return expected manifest doc_count and ordered_keys for batches."""
    all_rows: list[dict] = []
    for path in batch_paths:
        rows = load_records(path)
        if not validate_records(rows):
            continue
        all_rows.extend(rows)
    ordered = sort_keys([row["key"] for row in all_rows], collator_path)
    return {"doc_count": len(all_rows), "ordered_keys": ordered}
