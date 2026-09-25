"""Catalog admission and mark prepare (golden)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from sheet import seed as seed_mod


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_entries(catalog: dict, set_name: str) -> list[dict]:
    for impose_set in catalog["impose_sets"]:
        if impose_set["name"] == set_name:
            return list(impose_set["marks"])
    raise KeyError(set_name)


def rotate_cw(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.ROTATE_270)


def resize_nearest(img: Image.Image, nw: int, nh: int) -> Image.Image:
    return img.resize((nw, nh), Image.Resampling.NEAREST)


def prepare_marks(
    catalog: dict,
    entries: list[dict],
    marks_dir: Path,
    seed: int,
    pad: int,
) -> list[dict]:
    scale = seed_mod.scale_factor(catalog, seed)
    prepared: list[dict] = []
    for entry in entries:
        img = Image.open(marks_dir / entry["file"]).convert("RGBA")
        if entry["mark_id"] in catalog["scalable"]:
            nw = seed_mod.scaled_dim(img.width, scale)
            nh = seed_mod.scaled_dim(img.height, scale)
            img = resize_nearest(img, nw, nh)
        if entry["press_rotate"]:
            img = rotate_cw(img)
        cw, ch = img.size
        prepared.append(
            {
                "mark_id": entry["mark_id"],
                "frame": entry["frame"],
                "press_rotate": entry["press_rotate"],
                "content_w": cw,
                "content_h": ch,
                "padded_w": cw + 2 * pad,
                "padded_h": ch + 2 * pad,
                "image": img,
            }
        )
    prepared.sort(key=lambda s: (s["mark_id"], s["frame"]))
    return prepared
