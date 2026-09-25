"""Independent reference sprite atlas packer."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from PIL import Image


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def padding_px(catalog: dict, seed: int) -> int:
    return catalog["base_padding"] + (seed % catalog["padding_stride"])


def scale_factor(catalog: dict, seed: int) -> int:
    return 1 + (seed % catalog["scale_mod"])


def scaled_dim(base: int, scale: int) -> int:
    return max(1, base * scale)


def rotate_cw(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.ROTATE_270)


def resize_nearest(img: Image.Image, nw: int, nh: int) -> Image.Image:
    return img.resize((nw, nh), Image.Resampling.NEAREST)


def load_entries(catalog: dict, set_name: str) -> list[dict]:
    for pack_set in catalog["pack_sets"]:
        if pack_set["name"] == set_name:
            return list(pack_set["sprites"])
    raise KeyError(set_name)


def prepare_sprites(
    catalog: dict,
    entries: list[dict],
    sprites_dir: Path,
    seed: int,
    pad: int,
) -> list[dict]:
    scale = scale_factor(catalog, seed)
    prepared: list[dict] = []
    for entry in entries:
        img = Image.open(sprites_dir / entry["file"]).convert("RGBA")
        if entry["glyph_id"] in catalog["scalable"]:
            nw = scaled_dim(img.width, scale)
            nh = scaled_dim(img.height, scale)
            img = resize_nearest(img, nw, nh)
        if entry["rotate"]:
            img = rotate_cw(img)
        cw, ch = img.size
        prepared.append(
            {
                "glyph_id": entry["glyph_id"],
                "frame": entry["frame"],
                "rotate": entry["rotate"],
                "content_w": cw,
                "content_h": ch,
                "padded_w": cw + 2 * pad,
                "padded_h": ch + 2 * pad,
                "image": img,
            }
        )
    prepared.sort(key=lambda s: (s["glyph_id"], s["frame"]))
    return prepared


def ensure_fits(catalog: dict, sprites: list[dict]) -> None:
    limit = catalog["max_sprite_px"]
    for sprite in sprites:
        if sprite["padded_w"] > limit or sprite["padded_h"] > limit:
            raise OversizedError(
                f"{sprite['glyph_id']}:{sprite['frame']} exceeds max {limit}"
            )


class OversizedError(Exception):
    pass


def layout_sprites(sprites: list[dict], atlas_w: int, atlas_h: int) -> list[dict]:
    cursor_x = 0
    cursor_y = 0
    row_h = 0
    placed: list[dict] = []
    for sprite in sprites:
        if sprite["rotate"]:
            slot_w, slot_h = sprite["padded_h"], sprite["padded_w"]
        else:
            slot_w, slot_h = sprite["padded_w"], sprite["padded_h"]
        if cursor_x + slot_w > atlas_w:
            cursor_x = 0
            cursor_y += row_h
            row_h = 0
        if cursor_y + slot_h > atlas_h:
            raise RuntimeError("atlas overflow")
        placed.append(
            {
                "glyph_id": sprite["glyph_id"],
                "frame": sprite["frame"],
                "atlas_x": cursor_x,
                "atlas_y": cursor_y,
                "content_w": sprite["content_w"],
                "content_h": sprite["content_h"],
                "rotate": sprite["rotate"],
                "image": sprite["image"],
            }
        )
        cursor_x += slot_w
        row_h = max(row_h, slot_h)
    return placed


def uv_rect(
    atlas_x: int,
    atlas_y: int,
    content_w: int,
    content_h: int,
    atlas_w: int,
    atlas_h: int,
    pad: int,
) -> tuple[float, float, float, float]:
    inner_x = atlas_x + pad
    inner_y = atlas_y + pad
    aw = float(atlas_w)
    ah = float(atlas_h)
    return (
        inner_x / aw,
        inner_y / ah,
        (inner_x + content_w) / aw,
        (inner_y + content_h) / ah,
    )


def blit_with_bleed(
    atlas: Image.Image,
    atlas_x: int,
    atlas_y: int,
    pad: int,
    content_w: int,
    content_h: int,
    src: Image.Image,
) -> None:
    px = src.load()
    apx = atlas.load()
    for dy in range(-pad, content_h + pad):
        for dx in range(-pad, content_w + pad):
            sx = min(max(dx, 0), content_w - 1)
            sy = min(max(dy, 0), content_h - 1)
            color = px[sx, sy]
            tx = atlas_x + pad + dx
            ty = atlas_y + pad + dy
            if 0 <= tx < atlas.width and 0 <= ty < atlas.height:
                apx[tx, ty] = color


def compose_atlas(
    layout: list[dict],
    atlas_w: int,
    atlas_h: int,
    pad: int,
) -> Image.Image:
    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    for item in layout:
        blit_with_bleed(
            atlas,
            item["atlas_x"],
            item["atlas_y"],
            pad,
            item["content_w"],
            item["content_h"],
            item["image"],
        )
    return atlas


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
        u0, v0, u1, v1 = uv_rect(
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


def reference_pack(
    catalog_path: Path,
    sprites_dir: Path,
    set_name: str,
    seed: int,
) -> tuple[Image.Image, dict]:
    catalog = load_catalog(catalog_path)
    pad = padding_px(catalog, seed)
    entries = load_entries(catalog, set_name)
    prepared = prepare_sprites(catalog, entries, sprites_dir, seed, pad)
    ensure_fits(catalog, prepared)
    layout = layout_sprites(prepared, catalog["atlas_width"], catalog["atlas_height"])
    atlas = compose_atlas(layout, catalog["atlas_width"], catalog["atlas_height"], pad)
    manifest = build_manifest(catalog, layout, seed, pad)
    return atlas, manifest


def sample_bilinear(
    rgba: bytes,
    atlas_w: int,
    atlas_h: int,
    u0: float,
    v0: float,
    u1: float,
    v1: float,
    u: float,
    v: float,
) -> list[int]:
    px = u0 + u * (u1 - u0)
    py = v0 + v * (v1 - v0)
    fx = px * atlas_w - 0.5
    fy = py * atlas_h - 0.5
    x0 = max(int(fx // 1), 0)
    y0 = max(int(fy // 1), 0)
    x1 = min(x0 + 1, atlas_w - 1)
    y1 = min(y0 + 1, atlas_h - 1)
    tx = fx - x0
    ty = fy - y0

    def pix(x: int, y: int) -> list[int]:
        idx = (y * atlas_w + x) * 4
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


def reference_probe(
    atlas_path: Path,
    manifest: dict,
    glyph_id: str,
    frame: int,
    u: float,
    v: float,
) -> dict:
    entry = next(
        s for s in manifest["sprites"] if s["glyph_id"] == glyph_id and s["frame"] == frame
    )
    # decode png via PIL for probe reference
    img = Image.open(atlas_path).convert("RGBA")
    raw = img.tobytes()
    aw = manifest["atlas_width"]
    ah = manifest["atlas_height"]
    color = sample_bilinear(
        raw, aw, ah, entry["u0"], entry["v0"], entry["u1"], entry["v1"], u, v
    )
    return {
        "glyph_id": glyph_id,
        "frame": frame,
        "u": u,
        "v": v,
        "rgba": color,
    }
