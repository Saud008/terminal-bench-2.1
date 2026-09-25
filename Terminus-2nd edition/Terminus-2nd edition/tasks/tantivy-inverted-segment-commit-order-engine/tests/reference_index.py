"""
Independent inverted-index reference for tantool verifier tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class Doc:
    doc_id: int
    title: str
    body: str


@dataclass
class Segment:
    segment_id: str
    docs: List[Doc] = field(default_factory=list)
    postings: Dict[str, List[int]] = field(default_factory=dict)
    tombstones: List[int] = field(default_factory=list)
    field_norms: Dict[str, int] = field(default_factory=lambda: {"title": 1, "body": 2})


def tokenize_field(field: str, text: str) -> List[str]:
    prefix = "body:" if field == "body" else ""
    out: List[str] = []
    for raw in text.lower().split():
        tok = "".join(ch for ch in raw if ch.isalnum())
        if tok:
            out.append(f"{prefix}{tok}")
    return out


def build_postings(docs: List[Doc]) -> Dict[str, List[int]]:
    postings: Dict[str, List[int]] = {}
    for doc in docs:
        for term in tokenize_field("title", doc.title):
            postings.setdefault(term, []).append(doc.doc_id)
        for term in tokenize_field("body", doc.body):
            postings.setdefault(term, []).append(doc.doc_id)
    for term in postings:
        postings[term] = sorted(set(postings[term]))
    return postings


def load_batch(path: str | Path) -> Tuple[List[Doc], List[int]]:
    docs: List[Doc] = []
    tombstones: List[int] = []
    next_id = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        op = json.loads(line)
        if op["op"] == "add":
            docs.append(Doc(next_id, op["title"], op["body"]))
            next_id += 1
        elif op["op"] == "delete":
            tombstones.append(int(op["doc_id"]))
    tombstones = sorted(set(tombstones))
    return docs, tombstones


def segment_from_batch(path: str | Path, seg_id: str) -> Segment:
    docs, tombstones = load_batch(path)
    return Segment(
        segment_id=seg_id,
        docs=docs,
        postings=build_postings(docs),
        tombstones=tombstones,
    )


def remap_postings(postings: Dict[str, List[int]], offset: int) -> Dict[str, List[int]]:
    out: Dict[str, List[int]] = {}
    for term, ids in postings.items():
        out[term] = sorted(set(i + offset for i in ids))
    return out


def merge_postings(a: Dict[str, List[int]], b: Dict[str, List[int]]) -> Dict[str, List[int]]:
    out = {k: list(v) for k, v in a.items()}
    for term, ids in b.items():
        out.setdefault(term, []).extend(ids)
        out[term] = sorted(set(out[term]))
    return out


def live_doc_count(seg: Segment) -> int:
    dead = set(seg.tombstones)
    return sum(1 for d in seg.docs if d.doc_id not in dead)


def posting_checksum(seg: Segment) -> int:
    acc = 0
    for term in sorted(seg.postings.keys()):
        acc = (acc * 31 + len(term)) & 0xFFFFFFFFFFFFFFFF
        for doc_id in seg.postings[term]:
            acc = (acc * 131 + doc_id) & 0xFFFFFFFFFFFFFFFF
    return acc


def merge_segments(segs: List[Segment], merged_id: str = "ref-merged") -> Segment:
    all_docs: List[Doc] = []
    combined: Dict[str, List[int]] = {}
    all_tombs: List[int] = []
    offset = 0
    for seg in segs:
        for doc in seg.docs:
            all_docs.append(Doc(offset + doc.doc_id, doc.title, doc.body))
        remapped = remap_postings(seg.postings, offset)
        combined = merge_postings(combined, remapped)
        all_tombs.extend(offset + t for t in seg.tombstones)
        offset += len(seg.docs)
    all_tombs = sorted(set(all_tombs))
    return Segment(
        segment_id=merged_id,
        docs=all_docs,
        postings=combined,
        tombstones=all_tombs,
        field_norms={"title": 1, "body": 2},
    )


def search_term(seg: Segment, field: str, term: str) -> List[int]:
    key = f"body:{term.lower()}" if field == "body" else term.lower()
    dead = set(seg.tombstones)
    return sorted(i for i in seg.postings.get(key, []) if i not in dead)


def pipeline_from_batches(paths: List[Path]) -> Segment:
    segs = [segment_from_batch(p, f"seg-{i}") for i, p in enumerate(paths)]
    return merge_segments(segs)
