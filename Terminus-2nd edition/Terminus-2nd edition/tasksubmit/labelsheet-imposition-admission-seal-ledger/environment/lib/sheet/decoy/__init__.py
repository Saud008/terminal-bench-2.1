"""Decoy shelf helper — not on the impose/sample admission path."""


def legacy_shelf_key(mark_id: str, frame: int) -> str:
    return f"legacy:{mark_id}:{frame}"
