"""Independent reference for parquet-pushdown-scan filter."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_utc_ts(raw: str) -> datetime:
    if raw.endswith("Z"):
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(raw).astimezone(timezone.utc)


def should_skip_is_null(col: dict[str, Any]) -> bool:
    if not col.get("stats_present"):
        return False
    if col.get("null_count_omitted"):
        return False
    return int(col.get("null_count", 0)) == 0


def row_group_passes_ts_stats(col: dict[str, Any], bound: str) -> bool:
    if not col.get("stats_present"):
        return True
    if col.get("null_count_omitted"):
        return True
    return not (str(col.get("max", "")) < bound)


def canonical_page_order(order: list[str]) -> list[str]:
    seen: set[str] = set()
    canonical = ["null_bitmap", "dictionary", "data"]
    out: list[str] = []
    for page in canonical:
        if page in order and page not in seen:
            out.append(page)
            seen.add(page)
    for page in order:
        if page not in seen:
            out.append(page)
            seen.add(page)
    return out


def read_pages(rows: list[dict[str, Any]], col_name: str, col: dict[str, Any], want_null: bool) -> list[dict[str, Any]]:
    order = canonical_page_order(list(col.get("page_order", [])))
    working = [dict(r) for r in rows]
    for page in order:
        if page == "null_bitmap" and want_null:
            if col_name == "sensor_id":
                working = [r for r in working if r.get("sensor_id") is None]
            elif col_name == "hidden_flag":
                working = [r for r in working if r.get("hidden_flag") is None]
        elif page == "dictionary" and want_null and col_name == "sensor_id":
            continue
    return working


def split_chunks(rows: list[dict[str, Any]], chunk_size: int, workers: int) -> list[list[int]]:
    if workers <= 1 or not rows:
        return [[int(r["_row_id"]) for r in rows]]
    chunks: list[list[int]] = []
    for i in range(0, len(rows), chunk_size):
        chunk = [int(r["_row_id"]) for r in rows[i : i + chunk_size]]
        chunks.append(chunk)
    if len(chunks) <= workers:
        return chunks
    slices: list[list[int]] = [[] for _ in range(workers)]
    for i, ch in enumerate(chunks):
        slices[i % workers].extend(ch)
    return [s for s in slices if s]


def plan_checksum(plan: dict[str, Any]) -> str:
    raw = json.dumps(plan, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def reference_filter(catalog: dict[str, Any], spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    selected: list[int] = []
    pruned: list[int] = []
    is_null_col = spec.get("is_null_col") or ""
    ts_gte = spec.get("ts_gte") or ""
    workers = int(spec.get("workers") or 1)

    for rg in catalog["row_groups"]:
        rg_id = int(rg["id"])
        if is_null_col:
            col = rg["columns"].get(is_null_col, {})
            if should_skip_is_null(col):
                pruned.append(rg_id)
                continue
        selected.append(rg_id)

    if ts_gte:
        kept: list[int] = []
        for rg_id in selected:
            rg = next(r for r in catalog["row_groups"] if int(r["id"]) == rg_id)
            col = rg["columns"].get("measured_at", {})
            if row_group_passes_ts_stats(col, ts_gte):
                kept.append(rg_id)
            else:
                pruned.append(rg_id)
        selected = kept

    worker_slices: list[list[int]] = []
    chunk_size = int(catalog.get("chunk_size") or 1)
    for rg in catalog["row_groups"]:
        if int(rg["id"]) not in selected:
            continue
        col_chunk = chunk_size
        for c in rg["columns"].values():
            if int(c.get("chunk_size") or 0) > 0:
                col_chunk = int(c["chunk_size"])
                break
        worker_slices.extend(split_chunks(rg["rows"], col_chunk, workers))

    plan = {
        "table": catalog["table"],
        "selected_row_groups": selected,
        "page_read_order": ["null_bitmap", "dictionary", "data"],
        "worker_slices": worker_slices,
        "plan_written": True,
    }

    matched: set[int] = set()
    for rg in catalog["row_groups"]:
        if int(rg["id"]) not in selected:
            continue
        col_chunk = chunk_size
        for c in rg["columns"].values():
            if int(c.get("chunk_size") or 0) > 0:
                col_chunk = int(c["chunk_size"])
                break
        slices = split_chunks(rg["rows"], col_chunk, workers)
        slice_ids = {rid for s in slices for rid in s}
        for row in rg["rows"]:
            rid = int(row["_row_id"])
            if rid not in slice_ids:
                continue
            if ts_gte and parse_utc_ts(str(row["measured_at"])) < parse_utc_ts(ts_gte):
                continue
            if is_null_col:
                col = rg["columns"][is_null_col]
                hits = read_pages([row], is_null_col, col, True)
                if not hits:
                    continue
            matched.add(rid)

    result = {
        "table": catalog["table"],
        "matched_row_ids": sorted(matched),
        "row_count": len(matched),
        "pruned_row_groups": sorted(pruned),
        "plan_checksum": plan_checksum(plan),
    }
    return plan, result


def reference_filter_path(catalog_path: Path, spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    cat = json.loads(catalog_path.read_text(encoding="utf-8"))
    return reference_filter(cat, spec)
