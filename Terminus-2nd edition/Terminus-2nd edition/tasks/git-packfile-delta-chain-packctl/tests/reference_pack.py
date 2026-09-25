"""Independent reference pack resolver for packctl."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import zlib
from pathlib import Path
from typing import Any

KIND_BLOB = "blob"
KIND_TREE = "tree"
KIND_COMMIT = "commit"
KIND_OFS = "ofs_delta"
KIND_REF = "ref_delta"

ALLOWED_BASE = {KIND_BLOB, KIND_TREE, KIND_OFS, KIND_REF}


def sha1_hex(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def read_pack_object(stream: bytes, offset: int) -> tuple[int, bytes]:
    kind = stream[offset]
    (size,) = struct.unpack(">I", stream[offset + 1 : offset + 5])
    payload = zlib.decompress(stream[offset + 5 : offset + 5 + size])
    return kind, payload


def apply_patch(base: bytes, patch_text: bytes) -> bytes:
    out = bytearray()
    text = patch_text.decode("utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("COPY "):
            _, rest = line.split(" ", 1)
            off_s, len_s = rest.split()
            off, ln = int(off_s), int(len_s)
            out.extend(base[off : off + ln])
        elif line.startswith("INSERT "):
            out.extend(line[7:].encode("utf-8"))
        else:
            raise ValueError(f"bad patch line: {line}")
    return bytes(out)


def chain_depths(objects: list[dict[str, Any]]) -> list[int]:
    depths = [0] * len(objects)
    for _ in range(len(objects)):
        for i, obj in enumerate(objects):
            if obj["kind"] == KIND_REF and obj.get("base_id"):
                j = next(idx for idx, o in enumerate(objects) if o["id"] == obj["base_id"])
                depths[i] = max(depths[i], depths[j] + 1)
            elif obj["kind"] == KIND_OFS and obj.get("base_pack_offset") is not None:
                j = next(
                    idx for idx, o in enumerate(objects) if o["pack_offset"] == obj["base_pack_offset"]
                )
                depths[i] = max(depths[i], depths[j] + 1)
    return depths


def resolve_order(objects: list[dict[str, Any]]) -> list[int]:
    depths = chain_depths(objects)
    return sorted(range(len(objects)), key=lambda i: (depths[i], objects[i]["catalog_order"]))


def resolve_stage(stage_path: Path, stream_override: Path | None = None) -> list[dict[str, Any]]:
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    stream_path = stream_override or Path(stage["pack_stream_path"])
    stream = stream_path.read_bytes()
    objects = stage["objects"]
    order = resolve_order(objects)
    cache: dict[str, bytes] = {}
    depth_map: dict[str, int] = {}
    out: list[dict[str, Any]] = []

    for idx in order:
        obj = objects[idx]
        _, patch_or_raw = read_pack_object(stream, int(obj["pack_offset"]))
        if obj["kind"] in (KIND_BLOB, KIND_TREE):
            inflated = patch_or_raw
            depth = 0
        elif obj["kind"] == KIND_REF:
            base_id = obj["base_id"]
            base_obj = next(o for o in objects if o["id"] == base_id)
            if base_obj["kind"] not in ALLOWED_BASE:
                continue
            base_bytes = cache[base_id]
            inflated = apply_patch(base_bytes, patch_or_raw)
            depth = depth_map[base_id] + 1
        elif obj["kind"] == KIND_OFS:
            base_off = int(obj["base_pack_offset"])
            base_obj = next(o for o in objects if o["pack_offset"] == base_off)
            base_bytes = cache[base_obj["id"]]
            inflated = apply_patch(base_bytes, patch_or_raw)
            depth = depth_map[base_obj["id"]] + 1
        elif obj["kind"] == KIND_COMMIT:
            inflated = patch_or_raw
            depth = 0
        else:
            raise ValueError(obj["kind"])
        cache[obj["id"]] = inflated
        depth_map[obj["id"]] = depth
        out.append(
            {
                "id": obj["id"],
                "kind": obj["kind"],
                "inflated_size": len(inflated),
                "sha1": sha1_hex(inflated),
                "chain_depth": depth,
                "bytes": inflated,
            }
        )
    return out


def reference_export(stage_path: Path, *, id_salt: str = "") -> dict[str, Any]:
    rows = resolve_stage(stage_path)
    objects = []
    total = 0
    for row in rows:
        oid = row["id"] + id_salt if id_salt else row["id"]
        objects.append(
            {
                "id": oid,
                "kind": row["kind"],
                "inflated_size": row["inflated_size"],
                "sha1": row["sha1"],
                "chain_depth": row["chain_depth"],
            }
        )
        total += row["inflated_size"]
    objects.sort(key=lambda o: o["id"])
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    return {
        "pack_id": stage["pack_id"],
        "objects": objects,
        "total_inflated_bytes": total,
    }


def reference_delta_only(stream: bytes, offset: int, base: bytes) -> bytes:
    """Independent delta applicator for a single patch at offset."""
    _, patch = read_pack_object(stream, offset)
    return apply_patch(base, patch)


def tb3_salt() -> str:
    return os.environ.get("TB3_OBJECT_ID_SALT", "")
