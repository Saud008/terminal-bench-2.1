#!/usr/bin/env python3
"""Build pack.bundle fixtures for packctl task."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path

KIND_BLOB = 1
KIND_TREE = 2
KIND_COMMIT = 4
KIND_OFS = 6
KIND_REF = 7

ROOT = Path(__file__).resolve().parent.parent / "environment"


def sha1_hex(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def pack_object(kind: int, payload: bytes) -> bytes:
    compressed = zlib.compress(payload)
    return struct.pack(">BI", kind, len(compressed)) + compressed


def build_stream(entries: list[dict]) -> bytes:
    out = bytearray()
    for ent in entries:
        ent["pack_offset"] = len(out)
        out.extend(pack_object(ent["_kind"], ent["_payload"]))
        ent["compressed_size"] = len(out) - ent["pack_offset"] - 5
    return bytes(out)


def catalog_entry(ent: dict) -> dict:
    row = {
        "id": ent["id"],
        "kind": ent["kind"],
        "pack_offset": ent["pack_offset"],
        "compressed_size": ent["compressed_size"],
    }
    if ent.get("base_id"):
        row["base_id"] = ent["base_id"]
    if ent.get("base_pack_offset") is not None:
        row["base_pack_offset"] = ent["base_pack_offset"]
    return row


def write_bundle(pack_id: str, rel: str, entries: list[dict]) -> None:
    for ent in entries:
        if "id" not in ent:
            ent["id"] = sha1_hex(ent["_inflated"])
    stream = build_stream(entries)
    out_dir = ROOT / rel
    out_dir.mkdir(parents=True, exist_ok=True)
    catalog = {
        "pack_id": pack_id,
        "entries": [catalog_entry(e) for e in entries],
    }
    (out_dir / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    (out_dir / "pack.stream").write_bytes(stream)


def shallow() -> None:
    base = b"hello pack\n"
    base_id = sha1_hex(base)
    d1_patch = b"COPY 0 11\nINSERT !\n"
    d1_inflated = b"hello pack!\n"
    entries = [
        {"kind": "blob", "_kind": KIND_BLOB, "_payload": base, "_inflated": base, "id": base_id},
        {
            "kind": "ref_delta",
            "_kind": KIND_REF,
            "_payload": d1_patch,
            "_inflated": d1_inflated,
            "base_id": base_id,
        },
    ]
    write_bundle("shallow", "data/packs/shallow", entries)


def deep4() -> None:
    a = b"BASE0\n"
    aid = sha1_hex(a)
    b_patch = b"COPY 0 5\nINSERT 1\n"
    bid = sha1_hex(b"BASE01\n")
    c_patch = b"COPY 0 6\nINSERT 2\n"
    cid = sha1_hex(b"BASE012\n")
    d_patch = b"COPY 0 7\nINSERT 3\n"
    did = sha1_hex(b"BASE0123\n")
    trap = b"not a delta base\n"
    tid = sha1_hex(trap)
    trap_patch = b"COPY 0 4\nINSERT TRAP\n"
    entries = [
        {"kind": "blob", "_kind": KIND_BLOB, "_payload": a, "_inflated": a, "id": aid},
        {"kind": "ref_delta", "_kind": KIND_REF, "_payload": b_patch, "_inflated": b"BASE01\n", "base_id": aid},
        {"kind": "ref_delta", "_kind": KIND_REF, "_payload": c_patch, "_inflated": b"BASE012\n", "base_id": bid},
        {
            "kind": "ref_delta",
            "_kind": KIND_REF,
            "_payload": d_patch,
            "_inflated": b"BASE0123\n",
            "id": did,
            "base_id": cid,
        },
        {"kind": "commit", "_kind": KIND_COMMIT, "_payload": trap, "_inflated": trap, "id": tid},
        {
            "kind": "ref_delta",
            "_kind": KIND_REF,
            "_payload": trap_patch,
            "_inflated": b"not TRAP\n",
            "base_id": tid,
        },
    ]
    write_bundle("deep4", "verifier-fixtures/pack-bundles/deep4", entries)


def main() -> None:
    shallow()
    deep4()
    print("fixtures written under", ROOT)


if __name__ == "__main__":
    main()
