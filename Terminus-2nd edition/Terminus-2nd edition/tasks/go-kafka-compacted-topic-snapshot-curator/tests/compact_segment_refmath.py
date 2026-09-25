"""Golden math for offline Kafka-like compacted segment logs."""

from __future__ import annotations

import hashlib
import json
import os
import unicodedata
from pathlib import Path
from typing import Any

DEFAULT_RETENTION_MS = 600_000


def tomb_retention_window_ms() -> int:
    raw = os.environ.get("TB3_TOMB_RETENTION_MS", "")
    if raw:
        return int(raw)
    return DEFAULT_RETENTION_MS


def normalize_topic_key(raw: str) -> str:
    k = raw.strip()
    k = unicodedata.normalize("NFC", k)
    if k.startswith("user:"):
        k = "user:" + k[5:].lower()
    return k


def segment_files_numeric_order(names: list[str]) -> list[str]:
    def key(n: str) -> int:
        mid = n.removeprefix("seg_").removesuffix(".jsonl")
        return int(mid)

    return sorted(names, key=key)


def read_segment_jsonl(fixture_root: Path, scenario: str) -> list[dict[str, Any]]:
    seg_dir = fixture_root / "compact-logs" / scenario / "segments"
    names = segment_files_numeric_order([p.name for p in seg_dir.glob("seg_*.jsonl")])
    records: list[dict[str, Any]] = []
    for name in names:
        for line in (seg_dir / name).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rec["canonical_key"] = normalize_topic_key(rec["key_raw"])
            records.append(rec)
    return records


def golden_staging_digest(topic: str, scenario: str, fixture_root: Path) -> dict[str, Any]:
    records = read_segment_jsonl(fixture_root, scenario)
    staged = []
    for rec in records:
        staged.append(
            {
                "partition": rec["partition"],
                "offset": rec["offset"],
                "timestamp_ms": rec["timestamp_ms"],
                "key_raw": rec["key_raw"],
                "canonical_key": rec["canonical_key"],
                "value_raw": rec["value_raw"],
                "is_tombstone": rec["is_tombstone"],
            }
        )
    payload = {"topic": topic, "scenario": scenario, "records": staged}
    digest = hashlib.sha256(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
    return {
        "engine": "kcompactctl",
        "topic": topic,
        "scenario": scenario,
        "segment_count": len(list((fixture_root / "compact-logs" / scenario / "segments").glob("seg_*.jsonl"))),
        "record_count": len(staged),
        "records": staged,
        "staging_digest": digest,
    }


def _partition_offset_sort(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda r: (r["partition"], r["offset"]))


def _collapse_duplicate_offsets(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for rec in records:
        buckets.setdefault((rec["partition"], rec["offset"]), []).append(rec)
    out = []
    for key in sorted(buckets):
        group = buckets[key]
        best = group[0]
        for rec in group[1:]:
            if (
                rec["timestamp_ms"] > best["timestamp_ms"]
                or (
                    rec["timestamp_ms"] == best["timestamp_ms"]
                    and rec["canonical_key"] < best["canonical_key"]
                )
            ):
                best = rec
        out.append(best)
    return _partition_offset_sort(out)


def _partition_high_water(records: list[dict[str, Any]], part: int) -> int:
    return max((r["timestamp_ms"] for r in records if r["partition"] == part), default=0)


def _tombstone_within_window(rec: dict[str, Any], hi: int, window: int) -> bool:
    return rec["is_tombstone"] and rec["timestamp_ms"] >= hi - window


def golden_compact_snapshot(
    records: list[dict[str, Any]], window: int | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    window = tomb_retention_window_ms() if window is None else window
    ordered = _collapse_duplicate_offsets(_partition_offset_sort(records))
    latest: dict[str, dict[str, Any]] = {}
    for rec in ordered:
        latest[rec["canonical_key"]] = rec
    snapshot = []
    for ck in sorted(latest):
        rec = latest[ck]
        snapshot.append(
            {
                "canonical_key": ck,
                "partition": rec["partition"],
                "offset": rec["offset"],
                "value_raw": "" if rec["is_tombstone"] else rec["value_raw"],
                "deleted": rec["is_tombstone"],
            }
        )
    lineage = []
    parts = sorted({r["partition"] for r in ordered})
    for part in parts:
        hi = _partition_high_water(ordered, part)
        for rec in ordered:
            if rec["partition"] == part and _tombstone_within_window(rec, hi, window):
                lineage.append(
                    {
                        "canonical_key": rec["canonical_key"],
                        "partition": rec["partition"],
                        "offset": rec["offset"],
                        "timestamp_ms": rec["timestamp_ms"],
                    }
                )
    lineage.sort(key=lambda r: (r["partition"], r["offset"]))
    return snapshot, lineage


def golden_audit_findings(records: list[dict[str, Any]], window: int | None = None) -> list[dict[str, Any]]:
    window = tomb_retention_window_ms() if window is None else window
    findings: list[dict[str, Any]] = []
    collapsed = _collapse_duplicate_offsets(_partition_offset_sort(records))
    for i in range(1, len(collapsed)):
        if collapsed[i]["partition"] == collapsed[i - 1]["partition"] and collapsed[i]["offset"] < collapsed[i - 1]["offset"]:
            findings.append(
                {
                    "code": "offset_regress",
                    "partition": collapsed[i]["partition"],
                    "offset": collapsed[i]["offset"],
                    "detail": "partition_order_violation",
                }
            )
    counts: dict[tuple[int, int], int] = {}
    for rec in records:
        k = (rec["partition"], rec["offset"])
        counts[k] = counts.get(k, 0) + 1
        if counts[k] > 1:
            findings.append(
                {
                    "code": "dup_offset",
                    "partition": rec["partition"],
                    "offset": rec["offset"],
                    "detail": "duplicate_offset_seen",
                }
            )
    for part in sorted({r["partition"] for r in collapsed}):
        hi = _partition_high_water(collapsed, part)
        for rec in collapsed:
            if rec["partition"] == part and rec["is_tombstone"] and not _tombstone_within_window(rec, hi, window):
                findings.append(
                    {
                        "code": "tomb_expired",
                        "partition": part,
                        "offset": rec["offset"],
                        "detail": "outside_retention_window",
                    }
                )
    findings.sort(key=lambda f: (f["partition"], f["offset"], f["code"]))
    return findings


# Verifier-facing aliases (independent reference math naming contract)
reference_staging = golden_staging_digest
reference_compact = golden_compact_snapshot
reference_findings = golden_audit_findings
load_records = read_segment_jsonl
