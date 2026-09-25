"""Digest helpers shared with pytest minhash_ref contract."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any


def cluster_run_id(run_id: str, generation: int) -> str:
    body = f"{run_id}:{generation}".encode()
    return "grp-" + hashlib.sha256(body).hexdigest()[:12]


def nfkc_lower(raw: str) -> str:
    return unicodedata.normalize("NFKC", raw).lower()


def audit_digest_payload(report: dict[str, Any], member_lists: list[list[str]]) -> str:
    payload = {
        "cluster_count": report["cluster_count"],
        "cluster_run_id": report["cluster_run_id"],
        "jaccard_floor": report["jaccard_floor"],
        "member_lists": member_lists,
        "run_id": report["run_id"],
        "singleton_count": report["singleton_count"],
        "total_documents": report["total_documents"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
