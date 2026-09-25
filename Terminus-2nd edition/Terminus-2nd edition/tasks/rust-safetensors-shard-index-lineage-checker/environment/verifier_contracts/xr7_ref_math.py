"""Independent reference for safetensors shard index lineage checker."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

DTYPE_BYTES = {"F32": 4, "F16": 2, "BF16": 2, "I32": 4, "I64": 8, "U8": 1}


def parse_shard(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    header_len = struct.unpack("<Q", raw[:8])[0]
    header_bytes = raw[8 : 8 + header_len]
    payload = raw[8 + header_len :]
    header = json.loads(header_bytes.decode("utf-8"))
    return header, payload


def wx_anchor_fold(doc: dict) -> bool:
    return doc["base_model_hash"].lower() == doc["expected_base_model_hash"].lower()


def wx_payload_units(dtype: str, shape: list[int]) -> int:
    count = 1
    for d in shape:
        count *= int(d)
    return count * DTYPE_BYTES[dtype]


def payload_fingerprint(payload: bytes, start: int, end: int) -> str:
    return hashlib.sha256(payload[start:end]).hexdigest()


def load_manifests(mdir: Path) -> list[dict]:
    docs = []
    for path in sorted(mdir.glob("*.json")):
        docs.append(json.loads(path.read_text(encoding="utf-8")))
    return docs


def reference_journal(mdir: Path, sroot: Path) -> list[dict]:
    rows: list[dict] = []
    run_seq = 0
    for doc in load_manifests(mdir):
        for shard in doc["shards"]:
            shard_path = sroot / shard["shard_file"]
            header, payload = parse_shard(shard_path)
            for spec in shard["tensors"]:
                th = header[spec["name"]]
                start, end = th["data_offsets"]
                data_len = len(payload)
                if end > data_len:
                    raise ValueError(f"offset overflow {spec['name']}")
                expected = wx_payload_units(spec["dtype"], spec["shape"])
                if end - start != expected:
                    raise ValueError(f"dtype shape mismatch {spec['name']}")
                cs = payload_fingerprint(payload, start, end)
                rows.append(
                    {
                        "manifest_id": doc["manifest_id"],
                        "tensor": spec["name"],
                        "shard_file": shard["shard_file"],
                        "dtype": spec["dtype"],
                        "shape": spec["shape"],
                        "offset_start": start,
                        "offset_end": end,
                        "payload_fingerprint": cs,
                        "base_model_hash": doc["base_model_hash"],
                        "lineage_ok": wx_anchor_fold(doc),
                        "run_seq": run_seq,
                    }
                )
                run_seq += 1
    return rows


def reference_report(mdir: Path, sroot: Path, journal_rows: list[dict]) -> list[dict]:
    by_manifest: dict[str, list[dict]] = {}
    for row in journal_rows:
        by_manifest.setdefault(row["manifest_id"], []).append(row)
    reports = []
    for doc in load_manifests(mdir):
        mid = doc["manifest_id"]
        violations = []
        if not wx_anchor_fold(doc):
            violations.append(
                {
                    "tensor": "*",
                    "code": "LINEAGE_HASH",
                    "message": "base_model_hash does not match expected",
                }
            )
        for row in by_manifest.get(mid, []):
            shard_path = sroot / row["shard_file"]
            header, payload = parse_shard(shard_path)
            th = header.get(row["tensor"])
            if th is None:
                violations.append(
                    {
                        "tensor": row["tensor"],
                        "code": "MISSING_TENSOR",
                        "message": "tensor missing from shard header",
                    }
                )
                continue
            start, end = th["data_offsets"]
            if end > len(payload):
                violations.append(
                    {
                        "tensor": row["tensor"],
                        "code": "OFFSET_OVERFLOW",
                        "message": "tensor end exceeds data section",
                    }
                )
            expected = wx_payload_units(row["dtype"], row["shape"])
            if end - start != expected:
                violations.append(
                    {
                        "tensor": row["tensor"],
                        "code": "DTYPE_SHAPE",
                        "message": "payload span does not match dtype and shape",
                    }
                )
            cs = payload_fingerprint(payload, start, end)
            if cs != row["payload_fingerprint"]:
                violations.append(
                    {
                        "tensor": row["tensor"],
                        "code": "DIGEST",
                        "message": "payload fingerprint mismatch",
                    }
                )
        violations.sort(key=lambda v: (v["tensor"], v["code"]))
        rows_m = by_manifest.get(mid, [])
        reports.append(
            {
                "manifest_id": mid,
                "violations": violations,
                "totals": {
                    "violation_count": len(violations),
                    "tensor_count": len(rows_m),
                },
            }
        )
    return reports


def reference_pipeline(mdir: Path, sroot: Path) -> tuple[list[dict], list[dict]]:
    journal_rows = reference_journal(mdir, sroot)
    report = reference_report(mdir, sroot, journal_rows)
    return journal_rows, report
