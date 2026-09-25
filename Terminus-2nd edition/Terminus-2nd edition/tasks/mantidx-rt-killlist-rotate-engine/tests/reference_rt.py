"""Independent reference for mantidx RT index verifier tests."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def reference_hits(docs: Iterable[tuple[int, str, int]], query: str) -> list[int]:
    token = query.lower()
    hits = [
        doc_id
        for doc_id, body, killed in docs
        if killed == 0 and token in body.lower()
    ]
    return sorted(hits)


def merge_killlist_by_segment_order(entries: list[dict]) -> list[dict]:
    return sorted(entries, key=lambda e: (e["segment_order"], e["doc_id"]))
