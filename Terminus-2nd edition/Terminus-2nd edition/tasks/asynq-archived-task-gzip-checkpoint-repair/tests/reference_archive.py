"""Independent reference for Asynq archive bundle walk and manifest computation."""

from __future__ import annotations

import gzip
import io
import json
from pathlib import Path


def has_gzip_footer(data: bytes) -> bool:
    return len(data) >= 8


def read_member_tasks(bundle: bytes, offset: int, size: int) -> list[dict]:
    chunk = bundle[offset : offset + size]
    if not has_gzip_footer(chunk):
        raise ValueError("member missing gzip footer")
    with gzip.GzipFile(fileobj=io.BytesIO(chunk)) as gz:
        text = gz.read().decode("utf-8")
    out: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def load_index(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def last_win_tasks(bundle_path: Path, idx: dict) -> dict[str, dict]:
    bundle = bundle_path.read_bytes()
    final: dict[str, dict] = {}
    for member in idx.get("members", []):
        tasks = read_member_tasks(
            bundle, member["file_offset"], member["compressed_size"]
        )
        for row in tasks:
            final[row["id"]] = row
    return final


def reference_manifest(staging: dict, bundle_path: Path, idx_path: Path) -> dict:
    idx = load_index(idx_path)
    final = last_win_tasks(bundle_path, idx)
    ordered: list[str] = []
    for task_id in staging.get("ordered_ids", []):
        if task_id in final:
            ordered.append(task_id)
    priorities = {tid: final[tid]["priority"] for tid in ordered}
    retries = {tid: final[tid]["retry"] for tid in ordered}
    return {
        "seed": staging["seed"],
        "scenario": staging["scenario"],
        "ordered_ids": ordered,
        "priorities": priorities,
        "retries": retries,
    }


def member_footer_valid(bundle_path: Path, member: dict) -> bool:
    bundle = bundle_path.read_bytes()
    off = member["file_offset"]
    size = member["compressed_size"]
    if off + size > len(bundle):
        return False
    chunk = bundle[off : off + size]
    if not has_gzip_footer(chunk):
        return False
    try:
        read_member_tasks(bundle, off, size)
    except (OSError, ValueError, gzip.BadGzipFile):
        return False
    return True
