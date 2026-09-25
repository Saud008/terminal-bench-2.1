"""UV rectangle helpers."""

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
    aw = float(atlas_w)
    ah = float(atlas_h)
    return (
        atlas_x / aw,
        atlas_y / ah,
        (atlas_x + content_w + 2 * pad) / aw,
        (atlas_y + content_h + 2 * pad) / ah,
    )
