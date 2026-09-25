"""Shelf layout."""

from __future__ import annotations


def layout_marks(marks: list[dict], sheet_w: int, sheet_h: int) -> list[dict]:
    cursor_x = 0
    cursor_y = 0
    row_h = 0
    placed: list[dict] = []
    for mark in marks:
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
