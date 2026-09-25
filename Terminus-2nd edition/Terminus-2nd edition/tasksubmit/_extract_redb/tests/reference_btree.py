"""
Independent page-map reference for redbtool verifier tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

ORDER = 4


@dataclass
class BTree:
    root: Optional["Node"] = None
    height: int = 0


@dataclass
class Node:
    is_leaf: bool
    keys: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    children: List[Node] = field(default_factory=list)


def _split_leaf(entries: List[Tuple[str, str]]) -> Tuple[Node, str, Node]:
    n = len(entries)
    mid = n // 2
    left = Node(is_leaf=True, keys=[e[0] for e in entries[:mid]], values=[e[1] for e in entries[:mid]])
    promoted = entries[mid][0]
    right = Node(
        is_leaf=True,
        keys=[e[0] for e in entries[mid:]],
        values=[e[1] for e in entries[mid:]],
    )
    return left, promoted, right


def _split_internal(keys: List[str], children: List[Node]) -> Tuple[Node, str, Node]:
    n = len(keys)
    mid = n // 2
    promoted = keys[mid]
    left = Node(is_leaf=False, keys=keys[:mid], children=children[:mid + 1])
    right = Node(is_leaf=False, keys=keys[mid + 1:], children=children[mid + 1:])
    return left, promoted, right


def _child_index(keys: List[str], key: str) -> int:
    for i, k in enumerate(keys):
        if key < k:
            return i
    return len(keys)


def insert(tree: BTree, key: str, value: str) -> None:
    if tree.root is None:
        tree.root = Node(is_leaf=True, keys=[key], values=[value])
        tree.height = 1
        return
    new_root, split = _insert_node(tree.root, key, value)
    if split:
        promoted, right = split
        tree.root = Node(is_leaf=False, keys=[promoted], children=[new_root, right])
        tree.height += 1
    else:
        tree.root = new_root


def _insert_node(node: Node, key: str, value: str) -> Tuple[Node, Optional[Tuple[str, Node]]]:
    if node.is_leaf:
        keys = list(node.keys)
        values = list(node.values)
        for i, k in enumerate(keys):
            if k == key:
                values[i] = value
                return Node(is_leaf=True, keys=keys, values=values), None
        keys.append(key)
        values.append(value)
        paired = sorted(zip(keys, values), key=lambda x: x[0])
        keys = [p[0] for p in paired]
        values = [p[1] for p in paired]
        if len(keys) > ORDER:
            left, promoted, right = _split_leaf(list(zip(keys, values)))
            return left, (promoted, right)
        return Node(is_leaf=True, keys=keys, values=values), None

    idx = _child_index(node.keys, key)
    new_child, child_split = _insert_node(node.children[idx], key, value)
    keys = list(node.keys)
    children = list(node.children)
    children[idx] = new_child
    if child_split:
        promoted, right = child_split
        keys.insert(idx, promoted)
        children.insert(idx + 1, right)
        if len(keys) > ORDER:
            left, promoted_key, right = _split_internal(keys, children)
            return left, (promoted_key, right)
    return Node(is_leaf=False, keys=keys, children=children), None


def _min_keys() -> int:
    return (ORDER + 1) // 2


def _borrow_from_left(parent_keys: List[str], parent_children: List[Node], idx: int) -> None:
    sep = parent_keys[idx - 1]
    left = parent_children[idx - 1]
    right = parent_children[idx]
    if left.is_leaf:
        left.keys.pop()
        v = left.values.pop()
        right.keys.insert(0, sep)
        right.values.insert(0, v)
        parent_keys[idx - 1] = right.keys[0]
    else:
        moved_key = left.keys.pop()
        moved_child = left.children.pop()
        right.keys.insert(0, moved_key)
        right.children.insert(0, moved_child)
        parent_keys[idx - 1] = moved_key


def _borrow_from_right(parent_keys: List[str], parent_children: List[Node], idx: int) -> None:
    sep = parent_keys[idx]
    left = parent_children[idx]
    right = parent_children[idx + 1]
    if left.is_leaf:
        k = right.keys.pop(0)
        v = right.values.pop(0)
        left.keys.append(sep)
        left.values.append(v)
        parent_keys[idx] = k
    else:
        moved_key = right.keys.pop(0)
        moved_child = right.children.pop(0)
        left.keys.append(moved_key)
        left.children.append(moved_child)
        parent_keys[idx] = moved_key


def _merge_nodes(left: Node, sep: str, right: Node) -> Node:
    if left.is_leaf:
        keys = left.keys + [sep] + right.keys
        values = left.values + [""] + right.values
        return Node(is_leaf=True, keys=keys, values=values)
    keys = left.keys + [sep] + right.keys
    children = left.children + right.children
    return Node(is_leaf=False, keys=keys, children=children)


def _fix_underflow(parent_keys: List[str], parent_children: List[Node], idx: int) -> None:
    min_k = _min_keys()
    node = parent_children[idx]
    count = len(node.keys) if node.is_leaf else len(node.keys)
    if count >= min_k:
        return
    if idx > 0 and (parent_children[idx - 1].keys if parent_children[idx - 1].is_leaf else parent_children[idx - 1].keys):
        left = parent_children[idx - 1]
        left_count = len(left.keys)
        if left_count > min_k:
            _borrow_from_left(parent_keys, parent_children, idx)
            return
    if idx + 1 < len(parent_children):
        right = parent_children[idx + 1]
        if len(right.keys) > min_k:
            _borrow_from_right(parent_keys, parent_children, idx)
            return
    if idx > 0:
        sep = parent_keys.pop(idx - 1)
        left = parent_children.pop(idx - 1)
        right = parent_children.pop(idx - 1)
        parent_children[idx - 1] = _merge_nodes(left, sep, right)
        return
    sep = parent_keys.pop(idx)
    left = parent_children.pop(idx)
    right = parent_children.pop(idx)
    parent_children[idx] = _merge_nodes(left, sep, right)


def delete(tree: BTree, key: str) -> bool:
    if tree.root is None:
        return False
    new_root, removed = _delete_recursive(tree.root, key)
    tree.root = new_root
    if tree.root is None:
        tree.height = 0
    elif tree.height > 1 and not tree.root.is_leaf and not tree.root.keys and len(tree.root.children) == 1:
        tree.root = tree.root.children[0]
        tree.height -= 1
    return removed


def _delete_recursive(node: Node, key: str) -> Tuple[Optional[Node], bool]:
    if node.is_leaf:
        for i, k in enumerate(node.keys):
            if k == key:
                keys = list(node.keys)
                values = list(node.values)
                keys.pop(i)
                values.pop(i)
                if not keys:
                    return None, True
                return Node(is_leaf=True, keys=keys, values=values), True
        return node, False

    idx = _child_index(node.keys, key)
    if len(node.children) == 1:
        return _delete_recursive(node.children[0], key)
    if idx >= len(node.children):
        idx = len(node.children) - 1
    new_child, removed = _delete_recursive(node.children[idx], key)
    if not removed:
        return node, False
    keys = list(node.keys)
    children = list(node.children)
    if new_child is None:
        children.pop(idx)
        if idx < len(keys):
            keys.pop(idx)
        if len(children) == 1:
            return children[0], True
        return Node(is_leaf=False, keys=keys, children=children), True
    children[idx] = new_child
    _fix_underflow(keys, children, idx)
    return Node(is_leaf=False, keys=keys, children=children), True


def ordered_entries(tree: BTree) -> List[Dict[str, str]]:
    out: List[Tuple[str, str]] = []
    if tree.root:
        _collect(tree.root, out)
    out.sort(key=lambda x: x[0])
    dedup: Dict[str, str] = {}
    for k, v in out:
        dedup[k] = v
    return [{"key": k, "value": v} for k, v in sorted(dedup.items())]


def _collect(node: Node, out: List[Tuple[str, str]]) -> None:
    if node.is_leaf:
        for k, v in zip(node.keys, node.values):
            out.append((k, v))
    else:
        for child in node.children:
            _collect(child, out)


def leaf_count(tree: BTree) -> int:
    if not tree.root:
        return 0
    return _count_leaves(tree.root)


def _count_leaves(node: Node) -> int:
    if node.is_leaf:
        return 1
    return sum(_count_leaves(c) for c in node.children)


def apply_batch(tree: BTree, lines: List[dict]) -> None:
    """Last-op-wins: collapse puts, then delete only keys whose final op is delete."""
    collapsed: Dict[str, Optional[str]] = {}
    for row in lines:
        op = row["op"]
        if op == "put":
            collapsed[row["key"]] = row.get("value", "")
        elif op == "delete":
            collapsed[row["key"]] = None
    for key, value in sorted((k, v) for k, v in collapsed.items() if v is not None):
        insert(tree, key, value)
    for key, _value in sorted((k, v) for k, v in collapsed.items() if v is None):
        delete(tree, key)


def load_batch(path: str) -> List[dict]:
    rows: List[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            import json

            rows.append(json.loads(line))
    return rows
