"""Verifier reference math shipped under /app for pytest parity checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def expected_slots(shape: list[int], chunks: list[int]) -> int:
    slots = 1
    for dim, ch in zip(shape, chunks):
        slots *= ceil_div(dim, ch)
    return slots


def all_keys(shape: list[int], chunks: list[int]) -> list[str]:
    ni = ceil_div(shape[0], chunks[0])
    nj = ceil_div(shape[1], chunks[1])
    return [f"{i}.{j}" for i in range(ni) for j in range(nj)]


def missing_keys(manifest: dict) -> list[str]:
    present = set(manifest["chunk_keys"])
    return sorted(k for k in all_keys(manifest["shape"], manifest["chunks"]) if k not in present)


def compressor_fp(spec: dict) -> str:
    payload = f"{spec['id']}:{spec['level']}:{spec['shuffle']}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def world_value(index: int, coord: dict) -> float:
    return coord["transform"]["offset"] + coord["transform"]["scale"] * index


def span_for(coord: dict) -> list[float]:
    lo = world_value(0, coord)
    hi = world_value(int(coord["length"]) - 1, coord)
    return [min(lo, hi), max(lo, hi)]


def transform_ok(manifest: dict, axes_entry: dict) -> bool:
    if len(manifest["shape"]) != len(axes_entry["dims"]):
        return False
    for dim_name, shape_len in zip(axes_entry["dims"], manifest["shape"]):
        coord = axes_entry["coordinates"][dim_name]
        if int(coord["length"]) != int(shape_len):
            return False
    return True


def read_manifests(mdir: Path) -> list[dict]:
    rows = []
    for p in sorted(mdir.glob("*.json")):
        if p.name == "axes.json":
            continue
        rows.append(json.loads(p.read_text(encoding="utf-8")))
    rows.sort(key=lambda r: r["name"])
    return rows


def reference_staging(mdir: Path, axes_file: Path) -> list[dict]:
    axes = json.loads(axes_file.read_text(encoding="utf-8"))
    rows = []
    for manifest in read_manifests(mdir):
        axis = axes[manifest["name"]]
        span = {dim: span_for(axis["coordinates"][dim]) for dim in axis["dims"]}
        rows.append(
            {
                "array_name": manifest["name"],
                "shape": manifest["shape"],
                "chunks": manifest["chunks"],
                "expected_chunk_count": expected_slots(manifest["shape"], manifest["chunks"]),
                "present_chunk_count": len(manifest["chunk_keys"]),
                "missing_chunk_keys": missing_keys(manifest),
                "transform_ok": transform_ok(manifest, axis),
                "compressor_fingerprint": compressor_fp(manifest["compressor"]),
                "coordinate_span": span,
            }
        )
    rows.sort(key=lambda r: r["array_name"])
    return rows


def reference_manifest(mdir: Path, axes_file: Path) -> dict:
    staged = reference_staging(mdir, axes_file)
    arrays = []
    expected_sum = 0
    missing_sum = 0
    for row in staged:
        expected_sum += row["expected_chunk_count"]
        missing_sum += len(row["missing_chunk_keys"])
        arrays.append(
            {
                "name": row["array_name"],
                "shape": row["shape"],
                "chunks": row["chunks"],
                "missing_chunks": row["missing_chunk_keys"],
                "transform_ok": row["transform_ok"],
                "compressor_fingerprint": row["compressor_fingerprint"],
                "coordinate_span": row["coordinate_span"],
            }
        )
    arrays.sort(key=lambda a: a["name"])
    return {
        "version": 1,
        "arrays": arrays,
        "totals": {
            "array_count": len(arrays),
            "expected_chunks": expected_sum,
            "missing_chunks": missing_sum,
        },
    }
