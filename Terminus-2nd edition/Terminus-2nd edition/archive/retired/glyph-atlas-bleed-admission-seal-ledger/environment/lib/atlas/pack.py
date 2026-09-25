"""Shelf layout."""

from __future__ import annotations


def layout_sprites(sprites: list[dict], atlas_w: int, atlas_h: int) -> list[dict]:
    cursor_x = 0
    cursor_y = 0
    row_h = 0
    placed: list[dict] = []
    for sprite in sprites:
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
