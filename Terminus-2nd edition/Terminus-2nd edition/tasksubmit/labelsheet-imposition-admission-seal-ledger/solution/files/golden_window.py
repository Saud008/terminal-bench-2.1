"""Normalized sample window helpers (golden — inner content only)."""

from __future__ import annotations


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
