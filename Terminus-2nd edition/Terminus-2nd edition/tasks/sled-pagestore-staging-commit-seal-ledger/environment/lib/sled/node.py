from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BTree:
    root: dict[str, Any] | None = None
    height: int = 0


def leaf(entries: list[tuple[str, str]]) -> dict[str, Any]:
    return {"Leaf": {"entries": [[k, v] for k, v in entries]}}


def internal(keys: list[str], children: list[dict[str, Any]]) -> dict[str, Any]:
    high_key = subtree_max_key(children[-1]) if children else None
    return {"Internal": {"keys": keys, "children": children, "high_key": high_key}}


def is_leaf(node: dict[str, Any]) -> bool:
    return "Leaf" in node


def entries(node: dict[str, Any]) -> list[list[str]]:
    return node["Leaf"]["entries"]


def internal_parts(
    node: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]], str | None]:
    body = node["Internal"]
    return body["keys"], body["children"], body.get("high_key")


def key_count(node: dict[str, Any]) -> int:
    if is_leaf(node):
        return len(entries(node))
    keys, _, _ = internal_parts(node)
    return len(keys)


def subtree_max_key(node: dict[str, Any]) -> str | None:
    if is_leaf(node):
        ents = entries(node)
        return ents[-1][0] if ents else None
    _, children, high_key = internal_parts(node)
    if high_key is not None:
        return high_key
    return subtree_max_key(children[-1]) if children else None


def clone(node: dict[str, Any]) -> dict[str, Any]:
    import copy

    return copy.deepcopy(node)


def child_index(keys: list[str], key: str) -> int:
    for i, k in enumerate(keys):
        if key < k:
            return i
    return len(keys)
