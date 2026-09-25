from __future__ import annotations

import json

from sled import node
from sled.config import COMMIT_RECORD_PATH, PAGES_PATH


def run_commit_barrier(table: str, height: int, tree: node.BTree) -> None:
    COMMIT_RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMMIT_RECORD_PATH.write_text(
        json.dumps(
            {
                "table": table,
                "root_height": height,
                "children_fsynced": False,
                "height_recorded_before_child_fsync": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _flush_children(tree)


def _flush_children(tree: node.BTree) -> None:
    pages: dict[str, str] = {}
    if tree.root:
        _walk_pages(tree.root, "root", pages)
    PAGES_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAGES_PATH.write_text(json.dumps({"pages": pages}, indent=2), encoding="utf-8")


def _walk_pages(n: dict, pid: str, pages: dict[str, str]) -> None:
    if node.is_leaf(n):
        pages[pid] = f"leaf:{len(node.entries(n))}"
    else:
        keys, children, _ = node.internal_parts(n)
        pages[pid] = f"internal:{len(keys)}"
        for i, child in enumerate(children):
            _walk_pages(child, f"{pid}-{i}", pages)


def load_commit_record() -> dict | None:
    if not COMMIT_RECORD_PATH.is_file():
        return None
    return json.loads(COMMIT_RECORD_PATH.read_text(encoding="utf-8"))
