"""Sealed manifest builder (golden — canonical checksum)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from atlas import uv as uv_mod


def canonicalize(value):
    if isinstance(value, Mapping):
        return {k: canonicalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value


def manifest_checksum(body: dict) -> str:
    canonical = canonicalize(body)
    raw = json.dumps(canonical, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_manifest(
    catalog: dict,
    layout: list[dict],
    seed: int,
    pad: int,
) -> dict:
    aw = catalog["atlas_width"]
    ah = catalog["atlas_height"]
    sprites = []
    for item in layout:
        u0, v0, u1, v1 = uv_mod.uv_rect(
            item["atlas_x"],
            item["atlas_y"],
            item["content_w"],
            item["content_h"],
            aw,
            ah,
            pad,
        )
        sprites.append(
            {
                "glyph_id": item["glyph_id"],
                "frame": item["frame"],
                "atlas_x": item["atlas_x"],
                "atlas_y": item["atlas_y"],
                "content_w": item["content_w"],
                "content_h": item["content_h"],
                "rotate": item["rotate"],
                "u0": u0,
                "v0": v0,
                "u1": u1,
                "v1": v1,
            }
        )
    sprites.sort(key=lambda s: (s["glyph_id"], s["frame"]))
    body = {
        "atlas_width": aw,
        "atlas_height": ah,
        "padding_px": pad,
        "seed": seed,
        "sprites": sprites,
    }
    checksum = manifest_checksum(body)
    body["checksum"] = checksum
    return body


def write_manifest(path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def read_manifest(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
