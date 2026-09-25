from __future__ import annotations

from sled import node


def split_leaf(entries: list[tuple[str, str]]) -> tuple[dict, str, dict]:
    n = len(entries)
    if n <= 1:
        raise ValueError("leaf too small to split")
    left_size = (n + 1) // 2 if n % 2 == 1 else n // 2
    left_entries = entries[:left_size]
    promoted = entries[left_size][0]
    right_entries = entries[left_size:]
    return node.leaf(left_entries), promoted, node.leaf(right_entries)


def split_internal(keys: list[str], children: list[dict]) -> tuple[dict, str, dict]:
    n = len(keys)
    mid = (n + 1) // 2 if n % 2 == 1 else n // 2
    promoted = keys[mid]
    return (
        node.internal(keys[:mid], children[: mid + 1]),
        promoted,
        node.internal(keys[mid + 1 :], children[mid + 1 :]),
    )
