#!/usr/bin/env python3
"""Reference for dgraphguard tests."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_mutations_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        rows.append(
            {
                "graph": obj["graph"],
                "namespace": obj["namespace"],
                "partition_key": obj["partition_key"],
                "subject": obj["subject"],
                "predicate": obj["predicate"],
                "object_value": obj["object_value"],
                "object_lang": obj.get("object_lang", ""),
                "object_dtype": obj.get("object_dtype", ""),
                "mutation_uuid": obj["mutation_uuid"],
                "version": int(obj["version"]),
                "mutation_seq": int(obj["mutation_seq"]),
                "is_deleted": int(obj["is_deleted"]),
            }
        )
    return rows


def quad_key(r: dict[str, Any]) -> tuple[str, str, str, str]:
    return (r["graph"], r["namespace"], r["subject"], r["predicate"])


def blank_id(subject: str) -> int | None:
    m = re.fullmatch(r"_:b(\d+)", subject)
    return int(m.group(1)) if m else None


def row_beats(candidate: dict[str, Any], incumbent: dict[str, Any]) -> bool:
    if candidate["version"] != incumbent["version"]:
        return candidate["version"] > incumbent["version"]
    cb, ib = blank_id(candidate["subject"]), blank_id(incumbent["subject"])
    if cb is not None and ib is not None:
        return cb > ib
    if bool(candidate["object_dtype"]) != bool(incumbent["object_dtype"]):
        return bool(candidate["object_dtype"]) and not bool(incumbent["object_dtype"])
    if candidate["object_dtype"] != incumbent["object_dtype"]:
        return candidate["object_dtype"] > incumbent["object_dtype"]
    return candidate["mutation_uuid"] > incumbent["mutation_uuid"]


def coalesce_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for r in rows:
        k = quad_key(r)
        if k not in best or row_beats(r, best[k]):
            best[k] = r
    return sorted(best.values(), key=quad_key)


def update_barriers(barriers: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    idx = {(b["graph"], b["namespace"], b["partition_key"]): dict(b) for b in barriers}
    for r in rows:
        k = (r["graph"], r["namespace"], r["partition_key"])
        if k not in idx or r["version"] > idx[k]["max_mutation_version"]:
            idx[k] = {
                "graph": r["graph"],
                "namespace": r["namespace"],
                "partition_key": r["partition_key"],
                "max_mutation_version": r["version"],
            }
    return sorted(idx.values(), key=lambda b: (b["graph"], b["namespace"], b["partition_key"]))


def barrier_for_row(resume: dict[str, Any], row: dict[str, Any]) -> int | None:
    for b in resume.get("barriers", []):
        if (
            b["graph"] == row["graph"]
            and b["namespace"] == row["namespace"]
            and b["partition_key"] == row["partition_key"]
        ):
            return int(b["max_mutation_version"])
    return None


def filter_rows_by_resume(rows: list[dict[str, Any]], resume: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        barrier = barrier_for_row(resume, r)
        if barrier is not None and r["version"] < barrier:
            continue
        out.append(r)
    return out


def merge_resume_barriers(base: list[dict[str, Any]], resume: dict[str, Any]) -> list[dict[str, Any]]:
    idx = {(b["graph"], b["namespace"], b["partition_key"]): dict(b) for b in base}
    for rb in resume.get("barriers", []):
        k = (rb["graph"], rb["namespace"], rb["partition_key"])
        if k not in idx or rb["max_mutation_version"] >= idx[k]["max_mutation_version"]:
            idx[k] = {
                "graph": rb["graph"],
                "namespace": rb["namespace"],
                "partition_key": rb["partition_key"],
                "max_mutation_version": int(rb["max_mutation_version"]),
            }
    return sorted(idx.values(), key=lambda b: (b["graph"], b["namespace"], b["partition_key"]))


def snapshot_digest(barriers: list[dict[str, Any]], rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for b in barriers:
        lines.append(
            f"{b['graph']}|{b['namespace']}|{b['partition_key']}|{b['max_mutation_version']}"
        )
    for r in rows:
        lines.append(
            f"{r['graph']}|{r['namespace']}|{r['partition_key']}|{r['subject']}|{r['predicate']}|"
            f"{r['mutation_uuid']}|{r['version']}|{r['mutation_seq']}|{r['is_deleted']}|"
            f"{r['object_value']}|{r['object_lang']}|{r['object_dtype']}"
        )
    return sha256_hex("\n".join(lines).encode("utf-8"))


def replay_mutations(parts_path: Path, resume_path: Path | None = None) -> dict[str, Any]:
    batch = read_mutations_jsonl(parts_path)
    snap: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "barriers": [], "rows": [], "snapshot_digest": ""}
    if resume_path and resume_path.is_file():
        resume = json.loads(resume_path.read_text(encoding="utf-8"))
        snap["barriers"] = merge_resume_barriers(snap["barriers"], resume)
        snap["rows"] = list(resume.get("rows", []))
        batch = filter_rows_by_resume(batch, resume)
    coalesced = coalesce_rows(batch)
    if batch:
        snap["barriers"] = update_barriers(snap["barriers"], coalesced)
    merged = list(snap["rows"]) + coalesced
    snap["rows"] = coalesce_rows(merged)
    snap["snapshot_digest"] = snapshot_digest(snap["barriers"], snap["rows"])
    return snap


def entry_hash(row: dict[str, Any]) -> str:
    canon = (
        f"{row['subject']}|{row['predicate']}|{row['mutation_uuid']}|{row['version']}|"
        f"{row['is_deleted']}|{row['object_value']}|{row['object_lang']}|{row['object_dtype']}"
    )
    return sha256_hex(canon.encode("utf-8"))


def publish_snapshot(snap: dict[str, Any]) -> dict[str, Any]:
    entries = []
    for r in snap["rows"]:
        entries.append(
            {
                "subject": r["subject"],
                "predicate": r["predicate"],
                "mutation_uuid": r["mutation_uuid"],
                "version": r["version"],
                "is_deleted": r["is_deleted"],
                "object_value": r["object_value"],
                "object_lang": r["object_lang"],
                "object_dtype": r["object_dtype"],
                "ledger_sha256": entry_hash(r),
            }
        )
    root = sha256_hex("\n".join(e["ledger_sha256"] for e in entries).encode("utf-8"))
    return {"entries": entries, "ledger_root_sha256": root}
