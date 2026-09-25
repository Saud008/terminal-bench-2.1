"""Sealed ledger builder."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from sheet import window as window_mod


def canonicalize(value):
    if isinstance(value, Mapping):
        return {k: canonicalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value


def ledger_checksum(body: dict) -> str:
    raw = json.dumps(body, indent=2)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_ledger(
    catalog: dict,
    layout: list[dict],
    seed: int,
    pad: int,
) -> dict:
    aw = catalog["sheet_width"]
    ah = catalog["sheet_height"]
    marks = []
    for item in layout:
        u0, v0, u1, v1 = window_mod.window_rect(
            item["sheet_x"],
            item["sheet_y"],
            item["content_w"],
            item["content_h"],
            aw,
            ah,
            pad,
        )
        marks.append(
            {
                "mark_id": item["mark_id"],
                "frame": item["frame"],
                "sheet_x": item["sheet_x"],
                "sheet_y": item["sheet_y"],
                "content_w": item["content_w"],
                "content_h": item["content_h"],
                "press_rotate": item["press_rotate"],
                "u0": u0,
                "v0": v0,
                "u1": u1,
                "v1": v1,
            }
        )
    marks.sort(key=lambda s: (s["mark_id"], s["frame"]))
    body = {
        "sheet_width": aw,
        "sheet_height": ah,
        "gutter_px": pad,
        "seed": seed,
        "marks": marks,
    }
    checksum = ledger_checksum(body)
    body["checksum"] = checksum
    return body


def write_ledger(path, ledger: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")


def read_ledger(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
