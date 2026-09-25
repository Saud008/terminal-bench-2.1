"""Independent reference mark sheet imposer."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from PIL import Image


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gutter_px(catalog: dict, seed: int) -> int:
    return catalog["base_gutter"] + (seed % catalog["gutter_stride"])


def scale_factor(catalog: dict, seed: int) -> int:
    return 1 + (seed % catalog["scale_mod"])


def scaled_dim(base: int, scale: int) -> int:
    return max(1, base * scale)


def rotate_cw(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.ROTATE_270)


def resize_nearest(img: Image.Image, nw: int, nh: int) -> Image.Image:
    return img.resize((nw, nh), Image.Resampling.NEAREST)


def load_entries(catalog: dict, set_name: str) -> list[dict]:
    for impose_set in catalog["impose_sets"]:
        if impose_set["name"] == set_name:
            return list(impose_set["marks"])
    raise KeyError(set_name)


def prepare_marks(
    catalog: dict,
    entries: list[dict],
    marks_dir: Path,
    seed: int,
    pad: int,
) -> list[dict]:
    scale = scale_factor(catalog, seed)
    prepared: list[dict] = []
    for entry in entries:
        img = Image.open(marks_dir / entry["file"]).convert("RGBA")
        if entry["mark_id"] in catalog["scalable"]:
            nw = scaled_dim(img.width, scale)
            nh = scaled_dim(img.height, scale)
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


def ensure_fits(catalog: dict, marks: list[dict]) -> None:
    limit = catalog["max_mark_px"]
    for mark in marks:
        if mark["padded_w"] > limit or mark["padded_h"] > limit:
            raise OversizedError(
                f"{mark['mark_id']}:{mark['frame']} exceeds max {limit}"
            )


class OversizedError(Exception):
    pass


def layout_marks(marks: list[dict], sheet_w: int, sheet_h: int) -> list[dict]:
    cursor_x = 0
    cursor_y = 0
    row_h = 0
    placed: list[dict] = []
    for mark in marks:
        if mark["press_rotate"]:
            slot_w, slot_h = mark["padded_h"], mark["padded_w"]
        else:
            slot_w, slot_h = mark["padded_w"], mark["padded_h"]
        if cursor_x + slot_w > sheet_w:
            cursor_x = 0
            cursor_y += row_h
            row_h = 0
        if cursor_y + slot_h > sheet_h:
            raise RuntimeError("sheet overflow")
        placed.append(
            {
                "mark_id": mark["mark_id"],
                "frame": mark["frame"],
                "sheet_x": cursor_x,
                "sheet_y": cursor_y,
                "content_w": mark["content_w"],
                "content_h": mark["content_h"],
                "press_rotate": mark["press_rotate"],
                "image": mark["image"],
            }
        )
        cursor_x += slot_w
        row_h = max(row_h, slot_h)
    return placed


def window_rect(
    sheet_x: int,
    sheet_y: int,
    content_w: int,
    content_h: int,
    sheet_w: int,
    sheet_h: int,
    pad: int,
) -> tuple[float, float, float, float]:
    inner_x = sheet_x + pad
    inner_y = sheet_y + pad
    aw = float(sheet_w)
    ah = float(sheet_h)
    return (
        inner_x / aw,
        inner_y / ah,
        (inner_x + content_w) / aw,
        (inner_y + content_h) / ah,
    )


def blit_with_gutter(
    sheet: Image.Image,
    sheet_x: int,
    sheet_y: int,
    pad: int,
    content_w: int,
    content_h: int,
    src: Image.Image,
) -> None:
    px = src.load()
    apx = sheet.load()
    for dy in range(-pad, content_h + pad):
        for dx in range(-pad, content_w + pad):
            sx = min(max(dx, 0), content_w - 1)
            sy = min(max(dy, 0), content_h - 1)
            color = px[sx, sy]
            tx = sheet_x + pad + dx
            ty = sheet_y + pad + dy
            if 0 <= tx < sheet.width and 0 <= ty < sheet.height:
                apx[tx, ty] = color


def compose_sheet(
    layout: list[dict],
    sheet_w: int,
    sheet_h: int,
    pad: int,
) -> Image.Image:
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    for item in layout:
        blit_with_gutter(
            sheet,
            item["sheet_x"],
            item["sheet_y"],
            pad,
            item["content_w"],
            item["content_h"],
            item["image"],
        )
    return sheet


def canonicalize(value):
    if isinstance(value, Mapping):
        return {k: canonicalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value


def ledger_checksum(body: dict) -> str:
    canonical = canonicalize(body)
    raw = json.dumps(canonical, separators=(",", ":"), sort_keys=True)
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
        u0, v0, u1, v1 = window_rect(
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


def reference_impose(
    catalog_path: Path,
    marks_dir: Path,
    set_name: str,
    seed: int,
) -> tuple[Image.Image, dict]:
    catalog = load_catalog(catalog_path)
    pad = gutter_px(catalog, seed)
    entries = load_entries(catalog, set_name)
    prepared = prepare_marks(catalog, entries, marks_dir, seed, pad)
    ensure_fits(catalog, prepared)
    layout = layout_marks(prepared, catalog["sheet_width"], catalog["sheet_height"])
    sheet = compose_sheet(layout, catalog["sheet_width"], catalog["sheet_height"], pad)
    ledger = build_ledger(catalog, layout, seed, pad)
    return sheet, ledger


def sample_bilinear(
    rgba: bytes,
    sheet_w: int,
    sheet_h: int,
    u0: float,
    v0: float,
    u1: float,
    v1: float,
    u: float,
    v: float,
) -> list[int]:
    px = u0 + u * (u1 - u0)
    py = v0 + v * (v1 - v0)
    fx = px * sheet_w - 0.5
    fy = py * sheet_h - 0.5
    x0 = max(int(fx // 1), 0)
    y0 = max(int(fy // 1), 0)
    x1 = min(x0 + 1, sheet_w - 1)
    y1 = min(y0 + 1, sheet_h - 1)
    tx = fx - x0
    ty = fy - y0

    def pix(x: int, y: int) -> list[int]:
        idx = (y * sheet_w + x) * 4
        return list(rgba[idx : idx + 4])

    c00 = pix(x0, y0)
    c10 = pix(x1, y0)
    c01 = pix(x0, y1)
    c11 = pix(x1, y1)
    out = []
    for i in range(4):
        top = c00[i] + (c10[i] - c00[i]) * tx
        bot = c01[i] + (c11[i] - c01[i]) * tx
        out.append(int(round(top + (bot - top) * ty)))
    return out


def reference_sample(
    sheet_path: Path,
    ledger: dict,
    mark_id: str,
    frame: int,
    u: float,
    v: float,
) -> dict:
    entry = next(
        s for s in ledger["marks"] if s["mark_id"] == mark_id and s["frame"] == frame
    )
    # decode png via PIL for sample reference
    img = Image.open(sheet_path).convert("RGBA")
    raw = img.tobytes()
    aw = ledger["sheet_width"]
    ah = ledger["sheet_height"]
    color = sample_bilinear(
        raw, aw, ah, entry["u0"], entry["v0"], entry["u1"], entry["v1"], u, v
    )
    return {
        "mark_id": mark_id,
        "frame": frame,
        "u": u,
        "v": v,
        "rgba": color,
    }
