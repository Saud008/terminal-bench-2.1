"""Independent reference math for partition mutation readiness."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CONFIG = Path("/app/fixtures/config")


def config_bundle_digest() -> str:
    h = hashlib.sha256()
    for name in ("lag_policy.json", "catalog.json", "anchor.txt"):
        h.update((CONFIG / name).read_bytes())
    return h.hexdigest()


def load_policy_bundle() -> dict:
    return {
        "lag": json.loads((CONFIG / "lag_policy.json").read_text(encoding="utf-8")),
        "anchor": (CONFIG / "anchor.txt").read_text(encoding="utf-8").strip(),
    }


def canonical_partition(table: str, keymap: dict[str, str]) -> str:
    body = [table]
    for col in sorted(keymap):
        body.append(f"{col}={keymap[col]}")
    return "|".join(body)


def read_jsonl_tree(folder: Path, suffix: str) -> list[dict]:
    out: list[dict] = []
    for path in sorted(folder.glob(f"*{suffix}")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def index_partitions(meta_dir: Path) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for row in read_jsonl_tree(meta_dir, ".part-meta.jsonl"):
        pid = canonical_partition(row["table_name"], row["partition_key"])
        slot = idx.setdefault(pid, {"table": row["table_name"], "parts": 0, "any_detached": False})
        slot["parts"] += row["part_count"]
        if row["detached"]:
            slot["any_detached"] = True
    return idx


def replica_lag_peaks(rep_dir: Path) -> dict[str, int]:
    buckets: dict[str, list[int]] = {}
    for row in read_jsonl_tree(rep_dir, ".replica-log.jsonl"):
        buckets.setdefault(row["partition_id"], []).append(row["lag_sec"])
    return {pid: max(vals) for pid, vals in buckets.items()}


def version_peaks(mutations: list[dict]) -> dict[str, int]:
    peaks: dict[str, int] = {}
    for row in mutations:
        pid = row["partition_id"]
        ver = row["mutation_version"]
        peaks[pid] = max(peaks.get(pid, ver), ver)
    return peaks


def classify_row(detached: bool, lag: int, threshold: int, version: int, peak: int) -> str:
    if detached:
        return "detached"
    if lag > threshold:
        return "suppressed"
    if version == peak:
        return "ready"
    return "pending"


def reference_reconcile_rows(meta_dir: Path, mut_dir: Path, rep_dir: Path) -> list[dict]:
    policy = load_policy_bundle()
    threshold = policy["lag"]["max_lag_sec"]
    parts = index_partitions(meta_dir)
    lags = replica_lag_peaks(rep_dir)
    mutations = read_jsonl_tree(mut_dir, ".mut-cmd.jsonl")
    peaks = version_peaks(mutations)
    rows: list[dict] = []
    for m in mutations:
        pid = m["partition_id"]
        if pid not in parts:
            continue
        info = parts[pid]
        lag = lags.get(pid, 0)
        state = classify_row(info["any_detached"], lag, threshold, m["mutation_version"], peaks[pid])
        rows.append({
            "mutation_id": m["mutation_id"],
            "partition_id": pid,
            "mutation_version": m["mutation_version"],
            "table_name": info["table"],
            "readiness_state": state,
            "replica_lag_max": lag,
            "part_count": info["parts"],
            "issued_at": m["issued_at"],
        })
    rows.sort(key=lambda r: (r["partition_id"], r["mutation_version"]))
    return rows
