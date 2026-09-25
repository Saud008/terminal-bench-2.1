from __future__ import annotations

from sled import node


def split_leaf(entries: list[tuple[str, str]]) -> tuple[dict, str, dict]:
    n = len(entries)
    if n <= 1:
        raise ValueError("leaf too small to split")
    mid = n // 2
    promoted = entries[mid][0]
    return node.leaf(entries[:mid]), promoted, node.leaf(entries[mid:])


def split_internal(keys: list[str], children: list[dict]) -> tuple[dict, str, dict]:
    n = len(keys)
    mid = n // 2
    promoted = keys[mid]
    return (
        node.internal(keys[:mid], children[: mid + 1]),
        promoted,
        node.internal(keys[mid + 1 :], children[mid + 1 :]),
    )
