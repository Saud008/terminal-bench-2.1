from __future__ import annotations

from sled import node, split, underflow
from sled.config import ORDER


def insert(tree: node.BTree, key: str, value: str) -> None:
    if tree.root is None:
        tree.root = node.leaf([(key, value)])
        tree.height = 1
        return
    new_root, split_promote = _insert_node(tree.root, key, value)
    if split_promote:
        promoted, right = split_promote
        tree.height += 1
        tree.root = node.internal([promoted], [new_root, right])
    else:
        tree.root = new_root


def _insert_node(
    root: dict, key: str, value: str
) -> tuple[dict, tuple[str, dict] | None]:
    if node.is_leaf(root):
        ents = [(e[0], e[1]) for e in node.entries(root)]
        for i, (k, _) in enumerate(ents):
            if k == key:
                ents[i] = (key, value)
                return node.leaf(ents), None
        ents.append((key, value))
        ents.sort(key=lambda x: x[0])
        if len(ents) > ORDER:
            left, promoted, right = split.split_leaf(ents)
            return left, (promoted, right)
        return node.leaf(ents), None

    keys, children, _ = node.internal_parts(root)
    idx = node.child_index(keys, key)
    new_child, child_split = _insert_node(children[idx], key, value)
    keys = list(keys)
    children = list(children)
    children[idx] = new_child
    if child_split:
        promoted, right = child_split
        keys.insert(idx, promoted)
        children.insert(idx + 1, right)
        if len(keys) > ORDER:
            left_i, promoted_i, right_i = split.split_internal(keys, children)
            return left_i, (promoted_i, right_i)
    return node.internal(keys, children), None


def delete(tree: node.BTree, key: str) -> bool:
    if tree.root is None:
        return False
    new_root, removed = underflow.delete_recursive(tree.root, key)
    tree.root = new_root
    if tree.root is None:
        tree.height = 0
    elif tree.height > 1 and not node.is_leaf(tree.root):
        keys, children, _ = node.internal_parts(tree.root)
        if not keys and len(children) == 1:
            tree.root = children[0]
            tree.height -= 1
    return removed


def collect_leaves(root: dict, out: list[tuple[str, str]]) -> None:
    if node.is_leaf(root):
        for e in node.entries(root):
            out.append((e[0], e[1]))
    else:
        _, children, _ = node.internal_parts(root)
        for child in children:
            collect_leaves(child, out)


def ordered_entries(tree: node.BTree) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if tree.root:
        collect_leaves(tree.root, out)
    out.sort(key=lambda x: x[0])
    seen: dict[str, str] = {}
    for k, v in out:
        seen[k] = v
    return list(seen.items())


def physical_entry_count(tree: node.BTree) -> int:
    out: list[tuple[str, str]] = []
    if tree.root:
        collect_leaves(tree.root, out)
    return len(out)


def unique_key_count(tree: node.BTree) -> int:
    return len(ordered_entries(tree))


def leaf_count(tree: node.BTree) -> int:
    if not tree.root:
        return 0

    def _count(n: dict) -> int:
        if node.is_leaf(n):
            return 1
        _, children, _ = node.internal_parts(n)
        return sum(_count(c) for c in children)

    return _count(tree.root)


def live_page_ids(tree: node.BTree) -> set[str]:
    ids: set[str] = set()

    def walk(n: dict, pid: str) -> None:
        ids.add(pid)
        if not node.is_leaf(n):
            _, children, _ = node.internal_parts(n)
            for i, child in enumerate(children):
                walk(child, f"{pid}-{i}")

    if tree.root:
        walk(tree.root, "root")
    return ids
