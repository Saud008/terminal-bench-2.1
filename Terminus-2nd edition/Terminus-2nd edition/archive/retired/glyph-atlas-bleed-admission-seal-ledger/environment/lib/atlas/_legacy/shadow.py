"""Legacy shadow sorter — not on the hot path."""


def shadow_sort_key(glyph_id: str) -> str:
    return f"shadow:{glyph_id}"
