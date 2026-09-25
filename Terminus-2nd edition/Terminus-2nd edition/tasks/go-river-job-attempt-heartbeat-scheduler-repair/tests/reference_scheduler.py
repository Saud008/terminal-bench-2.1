"""Independent reference scheduler matching /app/docs contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CATALOG_PATH = Path("/app/fixtures/seed-catalog.json")
BACKOFF_BASE_MS = 1000


def procedural_offset(seed: str) -> int:
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return int(digest[:8], 16) % 997


def load_catalog(path: Path = CATALOG_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_procedural_jobs(seed: str, catalog: list[dict[str, Any]] | None = None, *, now_ms: int = 0) -> list[dict[str, Any]]:
    catalog = catalog if catalog is not None else load_catalog()
    offset = procedural_offset(seed)
    jobs: list[dict[str, Any]] = []
    for i, spec in enumerate(catalog):
        kind = spec["kind"]
        jobs.append(
            {
                "id": f"{kind}-{i + 1:02d}",
                "kind": kind,
                "payload": f"{spec['payload']}:{seed}:{offset + i}",
                "priority": int(spec["priority"]) + (offset % 7),
                "state": "pending",
                "attempts": 0,
                "max_attempts": int(spec.get("max_attempts") or 5),
                "available_at_ms": now_ms,
                "created_at_ms": now_ms,
            }
        )
    return jobs


def backoff_delay_ms(attempt: int, base_ms: int = BACKOFF_BASE_MS) -> int:
    exp = max(0, min(30, attempt))
    return base_ms * (2**exp)


def backoff_delay_ms_broken(attempt: int, base_ms: int, now_ms: int) -> int:
    hour_bucket = max(1, min(30, now_ms // 3_600_000))
    return base_ms * (2**hour_bucket)


def select_next(jobs: list[dict[str, Any]]) -> dict[str, Any] | None:
    pending = [j for j in jobs if j["state"] == "pending" and j["available_at_ms"] <= 0]
    if not pending:
        return None
    return sorted(pending, key=lambda j: (j["priority"], j["id"]))[0]


def select_next_broken(jobs: list[dict[str, Any]]) -> dict[str, Any] | None:
    pending = [j for j in jobs if j["state"] == "pending" and j["available_at_ms"] <= 0]
    if not pending:
        return None
    return sorted(pending, key=lambda j: (-j["priority"], j["id"]), reverse=True)[0]


def apply_failure(job: dict[str, Any], *, now_ms: int, err: str) -> dict[str, Any]:
    out = dict(job)
    out["attempts"] = int(out["attempts"]) + 1
    out["last_error"] = err
    if out["attempts"] >= out["max_attempts"]:
        out["state"] = "poison"
        out["available_at_ms"] = 0
        return out
    out["state"] = "pending"
    out["available_at_ms"] = now_ms + backoff_delay_ms(out["attempts"])
    return out


def claim_order(seed: str) -> list[str]:
    jobs = build_procedural_jobs(seed, now_ms=0)
    order: list[str] = []
    leases: dict[str, str] = {}
    while True:
        for j in jobs:
            if j["state"] == "pending" and j["available_at_ms"] > 0:
                j["available_at_ms"] = 0
        pick = select_next(jobs)
        if pick is None:
            break
        pick["state"] = "running"
        leases[pick["id"]] = f"worker-{len(order)}"
        order.append(pick["id"])
        pick["state"] = "finished"
        leases.pop(pick["id"], None)
    return order


def expected_backoff_after_fail(attempts_before: int, now_ms: int) -> int:
    attempts_after = attempts_before + 1
    return now_ms + backoff_delay_ms(attempts_after)


def lease_rows_after_ack(job_ids_finished: list[str], active: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out = dict(active)
    for jid in job_ids_finished:
        out.pop(jid, None)
    return out
