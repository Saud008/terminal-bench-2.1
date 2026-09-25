"""Independent reference for Typesense typo-token fuzzy ranking repair."""

from __future__ import annotations

import hashlib
import json
import os
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Document:
    docid: str
    title: str
    body: str
    brand: str
    insertion_order: int = 0

    def searchable_text(self) -> str:
        return f"{self.title} {self.body}"


def typo_distance_limit() -> int:
    return int(os.environ.get("TB3_TYPO_DISTANCE", "1"))


def nfc_key(token: str) -> str:
    return unicodedata.normalize("NFC", token)


def dedupe_tokens(tokens: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for token in tokens:
        key = nfc_key(token)
        if key not in seen:
            seen.add(key)
            out.append(token)
    return out


def index_terms(text: str) -> list[str]:
    raw = [t.lower() for t in text.split() if t]
    return dedupe_tokens(raw)


def levenshtein(a: str, b: str) -> int:
    a_chars = list(a)
    b_chars = list(b)
    n = len(a_chars)
    m = len(b_chars)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    cur = [0] * (m + 1)
    for i in range(1, n + 1):
        cur[0] = i
        for j in range(1, m + 1):
            cost = 0 if a_chars[i - 1] == b_chars[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev, cur = cur, prev
    return prev[m]


def expand_token(token: str, vocabulary: list[str]) -> list[str]:
    if len(token) < 4:
        return [token]
    limit = typo_distance_limit()
    out = [token]
    for vocab in vocabulary:
        if vocab == token:
            continue
        if levenshtein(token, vocab) <= limit:
            out.append(vocab)
    return sorted(set(out))


def prefix_match_score(query_token: str, index_token: str) -> float:
    if not index_token.startswith(query_token):
        return 0.0
    if query_token == index_token:
        return 1.0
    q_len = max(len(query_token.encode("utf-8")), 1)
    t_len = max(len(index_token.encode("utf-8")), 1)
    return 0.5 + 0.5 * (q_len / t_len)


def token_match_weight(query_token: str, index_token: str, typo: bool) -> float:
    if query_token == index_token:
        return 1.0
    if typo:
        return 0.85
    return prefix_match_score(query_token, index_token)


def apply_tiebreak(hits: list[dict[str, Any]]) -> None:
    def sort_key(hit: dict[str, Any]) -> tuple[float, str]:
        return (-hit["score"], hit["docid"])

    hits.sort(key=sort_key)
    i = 0
    while i < len(hits):
        j = i + 1
        while j < len(hits) and abs(hits[i]["score"] - hits[j]["score"]) <= 1e-9:
            j += 1
        group = hits[i:j]
        group.sort(key=lambda h: h["docid"])
        hits[i:j] = group
        i = j


def rank_documents(
    docs: list[Document],
    query_tokens: list[str],
    expanded: list[list[str]],
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for doc in docs:
        doc_terms = index_terms(doc.searchable_text())
        score = 0.0
        for qi, qtok in enumerate(query_tokens):
            variants = expanded[qi]
            best = 0.0
            for dt in doc_terms:
                for variant in variants:
                    typo = variant != qtok
                    weight = token_match_weight(variant, dt, typo)
                    best = max(best, weight)
                if best >= 1.0:
                    break
            if best <= 0.0:
                score = 0.0
                break
            score += best
        if score > 0.0:
            hits.append({"docid": doc.docid, "score": score})
    apply_tiebreak(hits)
    return hits


def brand_matches(doc: Document, brand: str) -> bool:
    return doc.brand.casefold() == brand.casefold()


def facet_brand_counts(all_docs: list[Document], hits: list[dict[str, Any]]) -> dict[str, int]:
    hit_ids = {h["docid"] for h in hits}
    counts: Counter[str] = Counter()
    for doc in all_docs:
        if doc.docid in hit_ids:
            counts[doc.brand] += 1
    return dict(sorted(counts.items()))


def parse_line(raw: str, order: int) -> Document:
    obj = json.loads(raw)
    return Document(
        docid=str(obj["docid"]),
        title=str(obj.get("title", "")),
        body=str(obj.get("body", "")),
        brand=str(obj.get("brand", "default")),
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


def rebuild_token_index(docs: list[Document]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for doc in docs:
        for term in index_terms(doc.searchable_text()):
            mapping.setdefault(term, []).append(doc.docid)
    for ids in mapping.values():
        ids.sort()
        deduped: list[str] = []
        for docid in ids:
            if not deduped or deduped[-1] != docid:
                deduped.append(docid)
        ids[:] = deduped
    return mapping


def run_search(
    docs: list[Document],
    token_index: dict[str, list[str]],
    query: str,
    brand_filter: str | None = None,
) -> dict[str, Any]:
    query_tokens = [t.lower() for t in query.split() if t]
    if not query_tokens:
        raise ValueError("empty query")
    full_vocab = sorted(token_index.keys())
    expanded = [expand_token(token, full_vocab) for token in query_tokens]
    hits = rank_documents(docs, query_tokens, expanded)
    if brand_filter is not None:
        hits = [
            hit
            for hit in hits
            if any(
                doc.docid == hit["docid"] and brand_matches(doc, brand_filter)
                for doc in docs
            )
        ]
    facets = {"brand": facet_brand_counts(docs, hits)}
    return {
        "hits": hits,
        "facets": facets,
        "query": query,
        "filter_brand": brand_filter,
    }


def pipeline_reference(
    batch: Path,
    query: str,
    brand_filter: str | None = None,
) -> dict[str, Any]:
    docs = load_batch(batch)
    token_index = rebuild_token_index(docs)
    return run_search(docs, token_index, query, brand_filter)


def staging_snapshot(raw: bytes, docs: list[Document]) -> dict[str, Any]:
    terms = sorted({term for doc in docs for term in index_terms(doc.searchable_text())})
    return {
        "doc_count": len(docs),
        "batch_sha256": hashlib.sha256(raw).hexdigest(),
        "terms": terms,
        "written_before_index": True,
    }
