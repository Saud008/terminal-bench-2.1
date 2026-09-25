from __future__ import annotations

from sled import merge, node
from sled.config import ORDER


def delete_recursive(root: dict, key: str) -> tuple[dict | None, bool]:
    if node.is_leaf(root):
        ents = [(e[0], e[1]) for e in node.entries(root)]
        for i, (k, _) in enumerate(ents):
            if k == key:
                ents.pop(i)
                if not ents:
                    return None, True
                return node.leaf(ents), True
        return root, False

    keys, children, _ = node.internal_parts(root)
    if len(children) == 1:
        return delete_recursive(children[0], key)
    idx = node.child_index(keys, key)
    if idx >= len(children):
        idx = len(children) - 1
    new_child, removed = delete_recursive(children[idx], key)
    if not removed:
        return root, False
    keys = list(keys)
    children = list(children)
    if new_child is None:
        children.pop(idx)
        if idx > 0:
            keys.pop(idx - 1)
        elif keys:
            keys.pop(0)
        if len(children) == 1:
            return children[0], True
        return node.internal(keys, children), True
    children[idx] = new_child
    min_keys = (ORDER + 1) // 2
    if node.key_count(children[idx]) < min_keys:
        merge.borrow_from_sibling(keys, children, idx)
    return node.internal(keys, children), True
