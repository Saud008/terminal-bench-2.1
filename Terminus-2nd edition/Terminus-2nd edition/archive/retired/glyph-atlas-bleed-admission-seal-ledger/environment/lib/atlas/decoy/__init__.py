"""Decoy shelf helper — not on the pack/probe admission path."""


def legacy_shelf_key(glyph_id: str, frame: int) -> str:
    return f"legacy:{glyph_id}:{frame}"
