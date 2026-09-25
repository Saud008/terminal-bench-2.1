"""Independent reference for lumidmx demux and atlas export."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rotate_left(seq: str, shift: int) -> str:
    if not seq:
        return seq
    n = shift % len(seq)
    return seq[n:] + seq[:n]


def complement_base(base: str) -> str:
    table = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}
    return table.get(base, base)


def reverse_complement(seq: str) -> str:
    return "".join(complement_base(b) for b in reversed(seq))


def tb3_seed_shift_bias() -> int:
    raw = os.environ.get("TB3_UMI_SEED_SHIFT", "0")
    try:
        return int(raw)
    except ValueError:
        return 0


def resolve_effective_samples(staging: dict[str, Any], lane_id: str) -> list[dict[str, str]]:
    lane = next((row for row in staging["lanes"] if row["lane_id"] == lane_id), None)
    if lane is None:
        return list(staging["samples_global"])

    if staging["precedence_order"] == "lane_first":
        merged = [dict(row) for row in staging["samples_global"]]
        for ov in lane.get("overrides", []):
            hit = next((row for row in merged if row["sample_id"] == ov["sample_id"]), None)
            if hit is not None:
                hit["barcode"] = ov["barcode"]
            else:
                merged.append(dict(ov))
        return merged

    return list(staging["samples_global"])


def hamming_ignore_n(observed: str, expected: str) -> int:
    if len(observed) != len(expected):
        return 10**9
    dist = 0
    for a, b in zip(observed, expected):
        if a == "N" or b == "N":
            continue
        if a != b:
            dist += 1
    return dist


def match_sample(observed: str, samples: list[dict[str, str]], budget: int) -> str | None:
    best: tuple[str, int] | None = None
    for sample in samples:
        dist = hamming_ignore_n(observed, sample["barcode"])
        if dist <= budget:
            if best is None or dist < best[1]:
                best = (sample["sample_id"], dist)
    return best[0] if best else None


def filter_synced_pairs(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [p for p in pairs if p.get("r1_umi") and p.get("r2_umi")]


def lane_seed_shift(staging: dict[str, Any], lane_id: str) -> int:
    lane = next(row for row in staging["lanes"] if row["lane_id"] == lane_id)
    return int(lane["seed_shift"]) + tb3_seed_shift_bias()


def canonical_r1(umi: str, shift: int) -> str:
    return rotate_left(umi, shift)


def canonical_r2(umi: str, shift: int) -> str:
    return rotate_left(reverse_complement(umi), shift)


def pair_canonical(r1: str, r2: str) -> str:
    return r1 if r1 <= r2 else r2


def reference_demux(staging: dict[str, Any]) -> dict[str, Any]:
    synced = filter_synced_pairs(staging["pairs"])
    entries: list[dict[str, Any]] = []
    budget = int(staging["mismatch_budget"])

    for pair in synced:
        samples = resolve_effective_samples(staging, pair["lane_id"])
        sample_id = match_sample(pair["r1_barcode"], samples, budget)
        if sample_id is None:
            continue
        shift = lane_seed_shift(staging, pair["lane_id"])
        r1c = canonical_r1(pair["r1_umi"], shift)
        r2c = canonical_r2(pair["r2_umi"], shift)
        entries.append(
            {
                "pair_id": pair["pair_id"],
                "lane_id": pair["lane_id"],
                "sample_id": sample_id,
                "r1_canonical": r1c,
                "r2_canonical": r2c,
                "canonical_umi": pair_canonical(r1c, r2c),
            }
        )

    entries.sort(key=lambda e: e["pair_id"])
    clusters = reference_clusters(entries)
    return {
        "demux_seq": 1,
        "ingest_seq": staging["ingest_seq"],
        "entries": entries,
        "clusters": clusters,
    }


def reference_clusters(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[str]] = {}
    for entry in entries:
        key = (entry["sample_id"], entry["canonical_umi"])
        groups.setdefault(key, []).append(entry["pair_id"])

    clusters: list[dict[str, Any]] = []
    for (sample_id, canonical_umi), pair_ids in sorted(groups.items()):
        pair_ids = sorted(pair_ids)
        cluster_id = min(
            entry["canonical_umi"]
            for entry in entries
            if entry["pair_id"] in pair_ids
        )
        clusters.append(
            {
                "cluster_id": cluster_id,
                "sample_id": sample_id,
                "canonical_umi": canonical_umi,
                "pair_ids": pair_ids,
            }
        )
    clusters.sort(key=lambda c: c["cluster_id"])
    return clusters


def reference_contamination(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_umi: dict[str, set[str]] = {}
    for entry in entries:
        by_umi.setdefault(entry["canonical_umi"], set()).add(entry["sample_id"])

    flags: list[dict[str, Any]] = []
    for canonical_umi, sample_ids in sorted(by_umi.items()):
        if len(sample_ids) > 1:
            flags.append(
                {
                    "canonical_umi": canonical_umi,
                    "sample_ids": sorted(sample_ids),
                    "flag": "cross_sample",
                }
            )
    return flags


def reference_atlas(staging: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "atlas_version": 1,
        "ingest_seq": staging["ingest_seq"],
        "demux_seq": ledger["demux_seq"],
        "clusters": ledger["clusters"],
        "contamination_flags": reference_contamination(ledger["entries"]),
    }


def reference_digest(atlas: dict[str, Any]) -> str:
    payload = json.dumps(atlas, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def reference_digest_paths(staging_path: Path, ledger_path: Path) -> str:
    staging = load_json(staging_path)
    ledger = load_json(ledger_path)
    atlas = reference_atlas(staging, ledger)
    return reference_digest(atlas)
