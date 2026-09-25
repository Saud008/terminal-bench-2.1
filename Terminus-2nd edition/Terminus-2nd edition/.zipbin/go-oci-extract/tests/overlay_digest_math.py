"""Independent OCI manifest math for verifier reference checks."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path
from typing import Any


def normalize_path(raw: str) -> str:
    p = raw.strip()
    if not p or p == ".":
        return "/"
    if not p.startswith("/"):
        p = "/" + p
    parts: list[str] = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    if not parts:
        return "/"
    return "/" + "/".join(parts)


def member_kind(clean_path: str) -> tuple[str, str]:
    base = clean_path.rsplit("/", 1)[-1]
    if base == ".wh..wh..opq":
        parent = clean_path.rsplit("/", 1)[0] if "/" in clean_path[1:] else "/"
        return "opaque", parent
    if base.startswith(".wh."):
        parent = clean_path.rsplit("/", 1)[0] if "/" in clean_path[1:] else "/"
        name = base[4:]
        if parent == "/":
            return "whiteout", f"/{name}"
        return "whiteout", f"{parent}/{name}"
    return "file", ""


def load_members(tar_path: Path, layer_index: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with tarfile.open(tar_path, "r:*") as tf:
        for info in tf:
            if info.name in (".", "./"):
                continue
            clean = normalize_path(info.name)
            if clean in ("/", ""):
                continue
            kind, extra = member_kind(clean)
            if kind == "file" and info.isdir():
                kind = "dir"
            path = extra if kind == "opaque" else clean
            out.append(
                {
                    "layer_index": layer_index,
                    "path": path,
                    "type": kind,
                    "mode": info.mode & 0o777,
                    "uid": info.uid,
                    "gid": info.gid,
                    "target": extra if kind == "whiteout" else "",
                }
            )
    return out


def load_manifest_stack(stack_json: Path) -> list[dict[str, Any]]:
    cfg = json.loads(stack_json.read_text(encoding="utf-8"))
    base = stack_json.parent
    members: list[dict[str, Any]] = []
    for layer in cfg["layers"]:
        members.extend(load_members(base / layer["tar"], layer["index"]))
    return members


def overlay_merge(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_layer: dict[int, list[dict[str, Any]]] = {}
    max_layer = 0
    for m in members:
        by_layer.setdefault(m["layer_index"], []).append(m)
        max_layer = max(max_layer, m["layer_index"])

    view: dict[str, dict[str, Any]] = {}
    layer_of: dict[str, int] = {}

    for layer in range(max_layer + 1):
        batch = sorted(by_layer.get(layer, []), key=lambda x: x["path"])
        whiteouts: list[dict[str, Any]] = []
        opaques: list[dict[str, Any]] = []
        for m in batch:
            if m["type"] == "whiteout":
                whiteouts.append(m)
            elif m["type"] == "opaque":
                opaques.append(m)
            elif m["type"] in ("file", "dir"):
                view[m["path"]] = {
                    "path": m["path"],
                    "type": m["type"],
                    "mode": m["mode"],
                    "uid": m["uid"],
                    "gid": m["gid"],
                }
                layer_of[m["path"]] = layer
        for w in whiteouts:
            view.pop(w["target"], None)
            layer_of.pop(w["target"], None)
        for op in opaques:
            d = op["path"]
            for p in list(view.keys()):
                if p == d:
                    continue
                if p.startswith(d + "/") and layer_of.get(p, -1) < layer:
                    view.pop(p, None)
                    layer_of.pop(p, None)
    return sorted(view.values(), key=lambda e: e["path"])


def canonical_line(entry: dict[str, Any]) -> str:
    mode = entry["mode"]
    if isinstance(mode, int):
        mode = f"{mode:04o}"
    obj = {
        "gid": entry["gid"],
        "mode": mode,
        "path": entry["path"],
        "type": entry["type"],
        "uid": entry["uid"],
    }
    return json.dumps(obj, separators=(",", ":"), sort_keys=True)


def expected_manifest(stack_json: Path, replay_seq: int = 1) -> dict[str, Any]:
    merged = overlay_merge(load_manifest_stack(stack_json))
    entries = [
        {
            "path": e["path"],
            "type": e["type"],
            "mode": f"{e['mode']:04o}",
            "uid": e["uid"],
            "gid": e["gid"],
        }
        for e in merged
    ]
    lines = [canonical_line(e) for e in entries]
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return {"manifest_hash": digest, "replay_seq": replay_seq, "entries": entries}


def expected_paths(stack_json: Path) -> list[str]:
    return [e["path"] for e in expected_manifest(stack_json)["entries"]]


def digest_from_stack(stack_json: Path, replay_seq: int = 1) -> dict[str, Any]:
    return expected_manifest(stack_json, replay_seq=replay_seq)


def sorted_paths_from_stack(stack_json: Path) -> list[str]:
    return expected_paths(stack_json)


def golden_atlas_doc(stack_json: Path, replay_seq: int = 1) -> dict[str, Any]:
    return expected_manifest(stack_json, replay_seq=replay_seq)


def golden_entry_list(stack_json: Path) -> list[str]:
    return expected_paths(stack_json)


def reference_manifest(stack_json: Path, replay_seq: int = 1) -> dict[str, Any]:
    return golden_atlas_doc(stack_json, replay_seq=replay_seq)


def reference_paths(stack_json: Path) -> list[str]:
    return golden_entry_list(stack_json)
