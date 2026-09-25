"""UV rectangle helpers (golden — inner content only)."""

from __future__ import annotations


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
