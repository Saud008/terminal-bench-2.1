from __future__ import annotations

from sled import node
from sled.config import ORDER


def borrow_from_sibling(
    parent_keys: list[str], parent_children: list[dict], child_idx: int
) -> None:
    min_keys = (ORDER + 1) // 2
    if child_idx > 0 and node.key_count(parent_children[child_idx - 1]) > min_keys:
        _borrow_from_left(parent_keys, parent_children, child_idx)
        return
    if (
        child_idx + 1 < len(parent_children)
        and node.key_count(parent_children[child_idx + 1]) > min_keys
    ):
        _borrow_from_right(parent_keys, parent_children, child_idx)
        return
    if child_idx > 0:
        _merge_with_left(parent_keys, parent_children, child_idx)
    else:
        _merge_with_right(parent_keys, parent_children, child_idx)


def _borrow_from_left(
    parent_keys: list[str], parent_children: list[dict], child_idx: int
) -> None:
    sep = parent_keys[child_idx - 1]
    left = parent_children[child_idx - 1]
    right = parent_children[child_idx]
    new_left, new_right, new_sep = _move_from_left(left, sep, right)
    parent_children[child_idx - 1] = new_left
    parent_children[child_idx] = new_right
    parent_keys[child_idx - 1] = new_sep


def _borrow_from_right(
    parent_keys: list[str], parent_children: list[dict], child_idx: int
) -> None:
    sep = parent_keys[child_idx]
    left = parent_children[child_idx]
    right = parent_children[child_idx + 1]
    new_left, new_right, new_sep = _move_from_right(left, sep, right)
    parent_children[child_idx] = new_left
    parent_children[child_idx + 1] = new_right
    parent_keys[child_idx] = new_sep


def _merge_with_left(
    parent_keys: list[str], parent_children: list[dict], child_idx: int
) -> None:
    sep = parent_keys.pop(child_idx - 1)
    right = parent_children.pop(child_idx)
    left = parent_children.pop(child_idx - 1)
    parent_children.insert(child_idx - 1, _merge_nodes(left, sep, right))


def _merge_with_right(
    parent_keys: list[str], parent_children: list[dict], child_idx: int
) -> None:
    sep = parent_keys.pop(child_idx)
    right = parent_children.pop(child_idx)
    left = parent_children.pop(child_idx)
    parent_children.insert(child_idx, _merge_nodes(left, sep, right))


def _move_from_left(left: dict, sep: str, right: dict) -> tuple[dict, dict, str]:
    if node.is_leaf(left) and node.is_leaf(right):
        le = [(e[0], e[1]) for e in node.entries(left)]
        re = [(e[0], e[1]) for e in node.entries(right)]
        last = le.pop()
        re = [last] + re
        return node.leaf(le), node.leaf(re), re[0][0]
    lk, lc, _ = node.internal_parts(left)
    rk, rc, _ = node.internal_parts(right)
    lk = list(lk)
    lc = list(lc)
    last_key = lk.pop()
    moved_child = lc.pop()
    rk = [sep] + list(rk)
    rc = [moved_child] + list(rc)
    return node.internal(lk, lc), node.internal(rk, rc), last_key


def _move_from_right(left: dict, sep: str, right: dict) -> tuple[dict, dict, str]:
    if node.is_leaf(left) and node.is_leaf(right):
        le = [(e[0], e[1]) for e in node.entries(left)]
        re = [(e[0], e[1]) for e in node.entries(right)]
        first = re.pop(0)
        le.append(first)
        return node.leaf(le), node.leaf(re), re[0][0]
    lk, lc, _ = node.internal_parts(left)
    rk, rc, _ = node.internal_parts(right)
    rk = list(rk)
    rc = list(rc)
    new_sep = rk.pop(0)
    moved_child = rc.pop(0)
    lk = list(lk) + [sep]
    lc = list(lc) + [moved_child]
    return node.internal(lk, lc), node.internal(rk, rc), new_sep


def _merge_nodes(left: dict, sep: str, right: dict) -> dict:
    if node.is_leaf(left) and node.is_leaf(right):
        le = [(e[0], e[1]) for e in node.entries(left)]
        re = [(e[0], e[1]) for e in node.entries(right)]
        le.extend(re)
        return node.leaf(le)
    lk, lc, _ = node.internal_parts(left)
    rk, rc, _ = node.internal_parts(right)
    keys = list(lk) + [sep] + list(rk)
    children = list(lc) + list(rc)
    return node.internal(keys, children)
