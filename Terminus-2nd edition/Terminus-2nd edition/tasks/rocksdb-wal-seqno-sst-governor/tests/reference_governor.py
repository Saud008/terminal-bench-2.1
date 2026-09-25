"""Independent reference for rocksctl governor staging artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _prefix(key: str, *, prefix: str = "") -> str:
    if prefix:
        return f"{prefix}{key}"
    return key


def _select_sst(stage: dict[str, Any]) -> list[str]:
    watermark = int(stage["watermark_seqno"])
    eligible = [
        f for f in stage["sst_files"] if int(f["max_seqno"]) <= watermark
    ]
    return sorted(f["file_id"] for f in eligible)


def _sum_operands(operands: list[str]) -> str:
    total = sum(int(o) for o in operands)
    return str(total)


def _merge_value(op: dict[str, Any]) -> str:
    if not op.get("finalized", False):
        return _sum_operands(op.get("operands", []))
    return _sum_operands(op.get("operands", []))


def _range_hides(key: str, start: str, end: str) -> bool:
    return start <= key < end


def reference_governor(stage_path: Path, *, key_prefix: str = "") -> dict[str, Any]:
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    snapshot = int(stage["snapshot_seqno"])
    watermark = int(stage["watermark_seqno"])
    selected = _select_sst(stage)
    selected_set = set(selected)

    records: list[tuple[str, str, str, int, str]] = []

    wal_batches = sorted(stage["wal_batches"], key=lambda b: b["ingest_order"])
    for batch in wal_batches:
        if not batch.get("committed", False):
            continue
        if int(batch["seqno"]) > snapshot:
            continue
        cf = batch["cf"]
        for put in batch.get("puts", []):
            records.append(
                (
                    cf,
                    _prefix(put["key"], prefix=key_prefix),
                    put["value"],
                    int(put["seqno"]),
                    "put",
                )
            )
        for tomb in batch.get("point_tombstones", []):
            records.append(
                (
                    cf,
                    _prefix(tomb["key"], prefix=key_prefix),
                    "",
                    int(tomb["seqno"]),
                    "point",
                )
            )

    sst_files = sorted(stage["sst_files"], key=lambda f: f["ingest_order"])
    for sst in sst_files:
        if sst["file_id"] not in selected_set:
            continue
        cf = sst["cf"]
        for key in sst.get("keys", []):
            records.append(
                (
                    cf,
                    _prefix(key["key"], prefix=key_prefix),
                    key["value"],
                    int(key["seqno"]),
                    "put",
                )
            )
        for tomb in sst.get("point_tombstones", []):
            records.append(
                (
                    cf,
                    _prefix(tomb["key"], prefix=key_prefix),
                    "",
                    int(tomb["seqno"]),
                    "point",
                )
            )
        for rt in sst.get("range_tombstones", []):
            records.append(
                (cf, rt["start"], rt["end"], int(rt["seqno"]), "range")
            )
        for op in sst.get("merge_operands", []):
            records.append(
                (
                    cf,
                    op["key"],
                    _merge_value(op),
                    int(op["seqno"]),
                    "merge",
                )
            )

    point_tombs = [(cf, key, seq) for cf, key, _, seq, kind in records if kind == "point"]
    range_tombs = [(cf, start, end, seq) for cf, start, end, seq, kind in records if kind == "range"]

    visible_latest: dict[tuple[str, str], dict[str, Any]] = {}
    for cf, key, value, seqno, kind in records:
        if kind not in ("put", "merge"):
            continue
        hidden = False
        for p_cf, p_key, p_seq in point_tombs:
            if p_cf == cf and p_key == key and p_seq >= seqno:
                hidden = True
                break
        if hidden:
            continue
        for r_cf, start, end, r_seq in range_tombs:
            if r_cf == cf and r_seq >= seqno and _range_hides(key, start, end):
                hidden = True
                break
        if hidden:
            continue
        slot = visible_latest.get((cf, key))
        if slot is None or seqno >= int(slot["seqno"]):
            visible_latest[(cf, key)] = {"key": key, "value": value, "seqno": seqno}

    by_cf: dict[str, list[dict[str, Any]]] = {}
    for (cf, _), vis in sorted(visible_latest.items()):
        by_cf.setdefault(cf, []).append(vis)
    for keys in by_cf.values():
        keys.sort(key=lambda row: row["key"])

    reclaimed = sum(
        int(f["size_bytes"])
        for f in sst_files
        if f["file_id"] in selected_set
    )

    return {
        "snapshot_seqno": snapshot,
        "watermark_seqno": watermark,
        "selected_sst": selected,
        "visible_keys": by_cf,
        "reclaimed_bytes": reclaimed,
        "compact_pass": 0,
    }


def reference_checksum(stage_path: Path, *, key_prefix: str = "") -> str:
    report = reference_governor(stage_path, key_prefix=key_prefix)
    payload = json.dumps(report, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def tb3_prefix() -> str:
    return os.environ.get("TB3_KEY_PREFIX", "")
