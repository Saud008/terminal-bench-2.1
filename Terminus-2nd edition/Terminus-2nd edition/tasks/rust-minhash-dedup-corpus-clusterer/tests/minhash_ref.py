"""Independent MinHash clustering reference for minclus."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any

PRIME = 1_000_000_007
STRIP = set(".,!?;:'\"()[]{} ")


def nfkc_lower(raw: str) -> str:
    return unicodedata.normalize("NFKC", raw).lower()


def normalize_tokens(raw: str) -> list[str]:
    out: list[str] = []
    for piece in nfkc_lower(raw).split():
        token = piece.strip("".join(STRIP))
        if token:
            out.append(token)
    return out


def word_shingles(tokens: list[str], k: int) -> list[str]:
    if len(tokens) < k:
        return []
    return [" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)]


def row_coefficients(base_seed: int, row: int, salt: str) -> tuple[int, int]:
    seed = (base_seed * 0x9E3779B9 + row) & ((1 << 64) - 1)
    if salt:
        seed = (seed + len(salt)) & ((1 << 64) - 1)
    a = ((seed * 6364136223846793005 + 1) | 1) % PRIME
    b = (seed + 1442695040888963407) % PRIME
    return a, b


def hash_token(token: str, a: int, b: int) -> int:
    h = 0
    for byte in token.encode("utf-8"):
        h = (h * 31 + byte) & ((1 << 64) - 1)
    return (a * h + b) % PRIME


def minhash_signature(shingles: list[str], base_seed: int, num_hashes: int, salt: str) -> list[int]:
    if not shingles:
        return [((1 << 64) - 1)] * num_hashes
    sig: list[int] = []
    for row in range(num_hashes):
        a, b = row_coefficients(base_seed, row, salt)
        best = (1 << 64) - 1
        for sh in shingles:
            best = min(best, hash_token(sh, a, b))
        sig.append(best)
    return sig


def estimate_jaccard(a: list[int], b: list[int]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return matches / len(a)


def pick_representative(doc_ids: list[str]) -> str:
    return min(doc_ids)


def cluster_run_id(run_id: str, generation: int) -> str:
    body = f"{run_id}:{generation}".encode()
    return "grp-" + hashlib.sha256(body).hexdigest()[:12]


def config_fingerprint(shingle_k: int, num_hashes: int, base_seed: int) -> str:
    body = f"{shingle_k}:{num_hashes}:{base_seed}".encode()
    return hashlib.sha256(body).hexdigest()[:16]


def load_corpus_dir(path: Path) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for jsonl in sorted(path.glob("*.jsonl")):
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                docs.append(json.loads(line))
    docs.sort(key=lambda d: d["doc_id"])
    return docs


def min_pairwise(members: list[int], sigs: list[list[int]]) -> float:
    if len(members) < 2:
        return 0.0
    best = 1.0
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            best = min(best, estimate_jaccard(sigs[members[i]], sigs[members[j]]))
    return best


def reference_report(
    run_id: str,
    corpus_dir: Path,
    *,
    shingle_k: int = 5,
    num_hashes: int = 64,
    base_seed: int = 1337,
    jaccard_floor: float = 0.5,
    group_generation: int = 1,
    scan_generation: int = 1,
    salt: str = "",
) -> dict[str, Any]:
    docs = load_corpus_dir(corpus_dir)
    sketch_docs = []
    sigs: list[list[int]] = []
    for doc in docs:
        tokens = normalize_tokens(doc["text"])
        shingles = word_shingles(tokens, shingle_k)
        sig = minhash_signature(shingles, base_seed, num_hashes, salt)
        sigs.append(sig)
        sketch_docs.append(
            {
                "doc_id": doc["doc_id"],
                "token_count": len(tokens),
                "shingle_count": len(shingles),
                "signature": sig,
            }
        )

    n = len(docs)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edges: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            est = estimate_jaccard(sigs[i], sigs[j])
            if est >= jaccard_floor:
                edges.append((i, j))
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    cluster_rows = []
    for idx, members in enumerate(sorted(groups.values(), key=lambda m: min(docs[i]["doc_id"] for i in m))):
        member_ids = sorted(docs[i]["doc_id"] for i in members)
        rep = pick_representative(member_ids)
        cluster_rows.append(
            {
                "cluster_id": f"c{idx + 1:03}",
                "representative_doc_id": rep,
                "member_doc_ids": member_ids,
                "source_paths": [f"{corpus_dir}/docs.jsonl" for _ in member_ids],
                "min_pairwise_estimate": min_pairwise(members, sigs),
            }
        )

    cluster_rows.sort(key=lambda c: c["cluster_id"])
    singleton_count = sum(1 for c in cluster_rows if len(c["member_doc_ids"]) == 1)
    member_lists = [c["member_doc_ids"] for c in cluster_rows]
    digest_body = json.dumps(
        {
            "cluster_count": len(cluster_rows),
            "cluster_run_id": cluster_run_id(run_id, group_generation),
            "jaccard_floor": jaccard_floor,
            "member_lists": member_lists,
            "run_id": run_id,
            "singleton_count": singleton_count,
            "total_documents": n,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        "run_id": run_id,
        "cluster_run_id": cluster_run_id(run_id, group_generation),
        "jaccard_floor": jaccard_floor,
        "total_documents": n,
        "cluster_count": len(cluster_rows),
        "singleton_count": singleton_count,
        "clusters": cluster_rows,
        "audit_digest": hashlib.sha256(digest_body.encode()).hexdigest(),
        "scan_generation": scan_generation,
        "config_fingerprint": config_fingerprint(shingle_k, num_hashes, base_seed),
    }
