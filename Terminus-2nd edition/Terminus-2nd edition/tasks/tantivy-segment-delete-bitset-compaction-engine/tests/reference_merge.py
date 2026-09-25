"""Independent reference merge for tantictl staging artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _remap_local(local: int, max_doc: int, seed: int) -> int:
    if seed == 0:
        return local
    return (local + seed) % max(max_doc, 1)


def reference_stats(stage_path: Path, *, seed: int = 0) -> dict[str, Any]:
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    segments = sorted(stage["segments"], key=lambda s: s["ingest_order"])
    delete_bits: set[int] = set()
    term_map: dict[tuple[str, str], tuple[int, int]] = {}
    offset = 0
    for seg in segments:
        max_doc = int(seg["max_doc"])
        for local in seg.get("delete_bits", []):
            remapped = _remap_local(int(local), max_doc, seed)
            delete_bits.add(offset + remapped)
        for row in seg.get("terms", []):
            key = (row["field"], row["term"])
            live = int(row["freq"]) - int(row.get("deleted_hits", 0))
            term_map[key] = (term_map.get(key, (0, 0))[0] + live, int(row["norm"]))
        offset += max_doc
    live_max_doc = sum(int(s["max_doc"]) for s in segments)
    terms = [
        {"field": f, "term": t, "freq": freq, "norm": norm}
        for (f, t), (freq, norm) in sorted(term_map.items())
    ]
    return {
        "live_max_doc": live_max_doc,
        "delete_bits": sorted(delete_bits),
        "terms": terms,
        "merge_pass": 0,
    }


def reference_checksum(stage_path: Path, *, seed: int = 0) -> str:
    stats = reference_stats(stage_path, seed=seed)
    payload = json.dumps(stats, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def tb3_seed() -> int:
    raw = os.environ.get("TB3_SEGMENT_SEED", "0")
    try:
        return int(raw)
    except ValueError:
        return 0
