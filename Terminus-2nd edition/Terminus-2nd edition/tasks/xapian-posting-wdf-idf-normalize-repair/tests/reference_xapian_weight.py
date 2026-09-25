"""Independent reference for Xapian WDF-IDF normalize repair."""

from __future__ import annotations

import json
import math
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Document:
    docid: str
    body: str
    synonyms: dict[str, list[str]] = field(default_factory=dict)
    insertion_order: int = 0


def rare_cf() -> int:
    raw = os.environ.get("TB3_RARE_CF", "2")
    val = int(raw)
    if val < 0:
        raise ValueError("invalid rare cf")
    return val


def tokenize(body: str) -> list[str]:
    return [t.lower() for t in body.split()]


def positional_collapse(tokens: list[str]) -> list[str]:
    if not tokens:
        return []
    out: list[str] = []
    i = 0
    while i < len(tokens):
        term = tokens[i]
        out.append(term)
        i += 1
        while i < len(tokens) and tokens[i] == tokens[i - 1]:
            i += 1
    return out


def slot_counts(collapsed: list[str]) -> dict[str, int]:
    return dict(Counter(collapsed))


def wdf_map(body: str) -> dict[str, float]:
    collapsed = positional_collapse(tokenize(body))
    return {term: 1.0 + math.log(slots) for term, slots in slot_counts(collapsed).items()}


def rebuild_cf(documents: list[Document]) -> dict[str, int]:
    cf: dict[str, int] = {}
    for doc in documents:
        collapsed = positional_collapse(tokenize(doc.body))
        for term in set(collapsed):
            cf[term] = cf.get(term, 0) + 1
    return cf


def length_norm(body: str) -> float:
    collapsed = positional_collapse(tokenize(body))
    unique = len(set(collapsed)) or 1
    return 1.0 / math.sqrt(unique)


def effective_wdf(term: str, wdf: dict[str, float], synonyms: dict[str, list[str]]) -> float:
    best = wdf.get(term, 0.0)
    for alt in synonyms.get(term, []):
        best = max(best, wdf.get(alt, 0.0))
    return best


def idf(n: int, cf: int) -> float:
    return math.log((n + 1) / (cf + 1))


def parse_query(raw: str) -> tuple[str, list[str]]:
    upper = raw.upper()
    if " OR " in upper:
        mode = "OR"
        splitter = " OR "
    elif " AND " in upper:
        mode = "AND"
        splitter = " AND "
    else:
        raise ValueError("query needs AND or OR")
    terms = [t.strip().lower() for t in raw.split(splitter) if t.strip()]
    if not terms:
        raise ValueError("no terms")
    return mode, terms


def term_weight(effective: float, idf_val: float) -> float:
    if effective <= 0.0:
        return 0.0
    return effective * idf_val


def parse_line(raw: str, order: int) -> Document:
    obj = json.loads(raw)
    syns: dict[str, list[str]] = {}
    for key, val in (obj.get("synonyms") or {}).items():
        syns[key.lower()] = [str(x).lower() for x in val]
    return Document(
        docid=str(obj["docid"]),
        body=str(obj["body"]),
        synonyms=syns,
        insertion_order=order,
    )


def load_batch(path: Path) -> list[Document]:
    docs: list[Document] = []
    order = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        docs.append(parse_line(line, order))
        order += 1
    return docs


def run_query(documents: list[Document], query: str) -> dict[str, Any]:
    mode, terms = parse_query(query)
    n = len(documents)
    cf = rebuild_cf(documents)
    hits: list[dict[str, Any]] = []
    for doc in documents:
        wdf = wdf_map(doc.body)
        ln = length_norm(doc.body)
        raw = 0.0
        for term in terms:
            eff = effective_wdf(term, wdf, doc.synonyms)
            if mode == "AND" and eff <= 0.0:
                raw = 0.0
                break
            cf_val = cf.get(term, 0)
            raw += term_weight(eff, idf(n, cf_val))
        else:
            if raw > 0.0:
                hits.append({"docid": doc.docid, "score": raw * ln})
    hits.sort(key=lambda h: (-h["score"], h["docid"]))
    return {"hits": hits, "mode": mode, "query": query}


def pipeline_reference(batch: Path, query: str) -> dict[str, Any]:
    docs = load_batch(batch)
    return run_query(docs, query)
