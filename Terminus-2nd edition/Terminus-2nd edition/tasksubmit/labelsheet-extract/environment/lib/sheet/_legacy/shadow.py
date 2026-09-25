"""Legacy shadow sorter — not on the hot path."""


def shadow_sort_key(mark_id: str) -> str:
    return f"shadow:{mark_id}"
