"""Independent reference for qwindex token search and manifest lineage."""

from __future__ import annotations

import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def tokenize(body: str) -> list[str]:
    return [part.lower() for part in body.split()]


def reference_hits(docs: list[dict], query: str, exclude: set[int] | None = None) -> list[int]:
    exclude = exclude or set()
    needle = query.lower()
    hits: list[int] = []
    for row in docs:
        doc_id = int(row["doc_id"])
        if doc_id in exclude:
            continue
        if needle in tokenize(str(row["body"])):
            hits.append(doc_id)
    hits.sort()
    return hits


def merge_parent_lineage(left: str, right: str) -> str:
    return max(left, right)
