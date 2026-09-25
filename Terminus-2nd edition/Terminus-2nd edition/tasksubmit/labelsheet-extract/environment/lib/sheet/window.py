"""Normalized sample window helpers."""

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
    aw = float(sheet_w)
    ah = float(sheet_h)
    return (
        sheet_x / aw,
        sheet_y / ah,
        (sheet_x + content_w + 2 * pad) / aw,
        (sheet_y + content_h + 2 * pad) / ah,
    )
