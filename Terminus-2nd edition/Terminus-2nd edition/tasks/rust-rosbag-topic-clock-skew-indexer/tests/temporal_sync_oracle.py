"""Closed-form oracle for skew-cal multi-topic clock skew atlas emission."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path


def read_bag_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def apply_topic_remap(raw: str, remap: dict[str, str]) -> str:
    return remap.get(raw, raw)


def parse_message_stream(path: Path, remap: dict[str, str]) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        v = json.loads(line)
        rows.append(
            {
                "topic": apply_topic_remap(v["topic"], remap),
                "seq": int(v["seq"]),
                "header_stamp_ns": int(v["header_stamp_ns"]),
                "receive_stamp_ns": int(v["receive_stamp_ns"]),
                "relay_pass": int(v.get("relay_pass", 0)),
            }
        )
    return rows


def collapse_msg_index_collisions(rows: list[dict]) -> list[dict]:
    best: dict[tuple[str, int], dict] = {}
    for row in rows:
        key = (row["topic"], row["seq"])
        if key not in best or row["relay_pass"] > best[key]["relay_pass"]:
            best[key] = row
    out = list(best.values())
    out.sort(key=lambda r: (r["header_stamp_ns"], r["topic"]))
    return out


def enforce_strict_monotonic(rows: list[dict]) -> None:
    last: dict[str, int] = {}
    for row in rows:
        prev = last.get(row["topic"])
        if prev is not None and row["header_stamp_ns"] <= prev:
            raise ValueError(f"non-strict monotonic on {row['topic']}")
        last[row["topic"]] = row["header_stamp_ns"]


def tally_stream_gaps(rows: list[dict]) -> int:
    last_seq: dict[str, int] = {}
    drops = 0
    for row in sorted(rows, key=lambda r: (r["topic"], r["seq"])):
        prev = last_seq.get(row["topic"])
        if prev is not None and row["seq"] > prev + 1:
            drops += row["seq"] - prev - 1
        last_seq[row["topic"]] = row["seq"]
    return drops


def build_sync_windows(rows: list[dict], reference_topic: str, sync_window_ns: int) -> list[dict]:
    half = sync_window_ns // 2
    ref_rows = sorted(
        [r for r in rows if r["topic"] == reference_topic],
        key=lambda r: r["header_stamp_ns"],
    )
    pairs: list[dict] = []
    for rr in ref_rows:
        anchor = rr["header_stamp_ns"]
        by_topic: dict[str, dict] = {}
        for other in rows:
            if other["topic"] == reference_topic:
                continue
            delta = int(other["header_stamp_ns"]) - int(anchor)
            if abs(delta) <= half:
                cur = by_topic.get(other["topic"])
                if cur is None or abs(delta) < abs(cur["delta_ns"]):
                    by_topic[other["topic"]] = {
                        "ref_stamp_ns": anchor,
                        "topic": other["topic"],
                        "header_stamp_ns": other["header_stamp_ns"],
                        "delta_ns": delta,
                    }
        pairs.extend(by_topic.values())
    pairs.sort(key=lambda p: (p["ref_stamp_ns"], p["topic"], p["header_stamp_ns"]))
    return pairs


def fit_drift_regression(pairs: list[dict], min_samples: int = 3) -> list[dict]:
    by_topic: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for p in pairs:
        by_topic[p["topic"]].append((int(p["ref_stamp_ns"]), int(p["delta_ns"])))
    out: list[dict] = []
    for topic in sorted(by_topic):
        samples = by_topic[topic]
        if len(samples) < min_samples:
            continue
        xs = [float(s[0]) for s in samples]
        ys = [float(s[1]) for s in samples]
        n = len(xs)
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        den = sum((x - x_mean) ** 2 for x in xs)
        slope = 0.0 if abs(den) < 1e-9 else num / den
        intercept = y_mean - slope * x_mean
        out.append(
            {
                "topic": topic,
                "slope": slope,
                "intercept_ns": intercept,
                "sample_count": len(samples),
            }
        )
    return out


def compute_audit_digest(atlas: dict) -> str:
    topics = sorted(d["topic"] for d in atlas["drift_rows"])
    body = json.dumps(
        {
            "bag_id": atlas["bag_id"],
            "drop_count": atlas["drop_count"],
            "sync_pair_count": atlas["sync_pair_count"],
            "topics": topics,
        },
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode()).hexdigest()


def expected_skew_atlas(meta: dict, rows: list[dict], min_samples: int = 3) -> dict:
    pairs = build_sync_windows(rows, meta["reference_topic"], int(meta["sync_window_ns"]))
    drifts = fit_drift_regression(pairs, min_samples=min_samples)
    atlas = {
        "bag_id": meta["bag_id"],
        "reference_topic": meta["reference_topic"],
        "sync_window_ns": meta["sync_window_ns"],
        "drop_count": tally_stream_gaps(rows),
        "sync_pair_count": len(pairs),
        "drift_rows": drifts,
        "audit_digest": "",
    }
    atlas["audit_digest"] = compute_audit_digest(atlas)
    return atlas


def oracle_full_pipeline(meta_path: Path, stream_path: Path, min_samples: int = 3) -> tuple[dict, list[dict]]:
    meta = read_bag_manifest(meta_path)
    remap = meta.get("topic_remap", {})
    rows = collapse_msg_index_collisions(parse_message_stream(stream_path, remap))
    enforce_strict_monotonic(rows)
    return expected_skew_atlas(meta, rows, min_samples=min_samples), rows


# Verifier-facing aliases (G-026 reference_* helpers)
reference_pipeline = oracle_full_pipeline
reference_atlas = expected_skew_atlas
reference_match_sync = build_sync_windows
reference_dedupe_rows = collapse_msg_index_collisions
reference_load_meta = read_bag_manifest
reference_load_messages = parse_message_stream
