from __future__ import annotations

from sled import btree


def collapse_puts(ops: list[dict]) -> list[tuple[str, str]]:
    collapsed: dict[str, str] = {}
    for op in ops:
        if op["op"] == "put":
            collapsed[op["key"]] = op.get("value", "")
    return list(collapsed.items())


def append_put(tree, key: str, value: str) -> None:
    btree.insert(tree, key, value)
