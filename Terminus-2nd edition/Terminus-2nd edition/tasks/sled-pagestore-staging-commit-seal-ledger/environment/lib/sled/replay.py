from __future__ import annotations

from sled import node


def collapse_puts(ops: list[dict]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for op in ops:
        if op["op"] == "put":
            out.append((op["key"], op.get("value", "")))
    return out


def append_put(tree: node.BTree, key: str, value: str) -> None:
    if tree.root is None:
        tree.root = node.leaf([(key, value)])
        tree.height = 1
        return
    _append_into(tree, key, value)


def _append_into(tree: node.BTree, key: str, value: str) -> None:
    assert tree.root is not None
    new_root, split_promote = _append_recursive(tree.root, key, value)
    if split_promote:
        promoted, right = split_promote
        tree.height += 1
        tree.root = node.internal([promoted], [new_root, right])
    else:
        tree.root = new_root


def _append_recursive(root: dict, key: str, value: str):
    from sled import split

    if node.is_leaf(root):
        ents = [(e[0], e[1]) for e in node.entries(root)]
        ents.append((key, value))
        ents.sort(key=lambda x: x[0])
        if len(ents) > 4:
            left, promoted, right = split.split_leaf(ents)
            return left, (promoted, right)
        return node.leaf(ents), None
    keys, children, _ = node.internal_parts(root)
    idx = node.child_index(keys, key)
    new_child, child_split = _append_recursive(children[idx], key, value)
    keys = list(keys)
    children = list(children)
    children[idx] = new_child
    if child_split:
        promoted, right = child_split
        keys.insert(idx, promoted)
        children.insert(idx + 1, right)
        if len(keys) > 4:
            left_i, promoted_i, right_i = split.split_internal(keys, children)
            return left_i, (promoted_i, right_i)
    return node.internal(keys, children), None
