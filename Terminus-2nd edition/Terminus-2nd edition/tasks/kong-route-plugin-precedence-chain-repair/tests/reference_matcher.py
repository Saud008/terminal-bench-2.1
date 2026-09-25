"""Independent reference for route matching and ingest validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


def seed_offset(seed: str, label: str) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()
    return int(digest[:8], 16)


def per_run_api_key(seed: str) -> str:
    return f"key-{seed_offset(seed, 'api') & 0xFFFFFF:06x}"


def hidden_deck_path(seed: str, tmp: Path) -> Path:
    token = format(seed_offset(seed, "hidden") % 10000, "04x")
    path = f"/api/v2/hidden/{token}"
    submit_path = f"{path}/submit"
    deck = {
        "services": [
            {
                "name": f"hidden-svc-{token}",
                "url": "http://127.0.0.1:8000/upstream/hidden",
                "plugins": [],
            }
        ],
        "routes": [
            {
                "name": f"hidden-get-{token}",
                "service": f"hidden-svc-{token}",
                "paths": [path],
                "methods": ["GET"],
                "scope_tags": [],
                "tags": ["hidden"],
                "plugins": [],
            },
            {
                "name": f"hidden-post-{token}",
                "service": f"hidden-svc-{token}",
                "paths": [path, submit_path],
                "methods": ["POST"],
                "scope_tags": [],
                "tags": ["hidden"],
                "plugins": [],
            },
        ],
        "consumers": [],
    }
    dest = tmp / f"hidden-deck-{token}.yaml"
    dest.write_text(yaml.safe_dump(deck), encoding="utf-8")
    return dest


def reference_match(routes: list[dict], method: str, req_path: str) -> str | None:
    max_len = 0
    for rt in routes:
        for p in rt["paths"]:
            if req_path.startswith(p) and len(p) > max_len:
                max_len = len(p)
    if max_len == 0:
        return None
    candidates: list[str] = []
    for rt in routes:
        best = max((len(p) for p in rt["paths"] if req_path.startswith(p)), default=0)
        if best != max_len:
            continue
        methods = rt.get("methods") or []
        if methods and method.upper() not in {m.upper() for m in methods}:
            continue
        candidates.append(rt["name"])
    if not candidates:
        return None
    return min(candidates)
