from __future__ import annotations

import json

from sled import checksum, node
from sled.config import REGISTRY_PATH


def load_registry() -> dict:
    if not REGISTRY_PATH.is_file():
        return {"pages": {}}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(reg: dict) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def persist_page(page_id: str, header: dict, body: str) -> None:
    reg = load_registry()
    cs = checksum.page_checksum(header, body.encode("utf-8"))
    reg["pages"][page_id] = {"header": header, "body": body, "checksum": cs}
    save_registry(reg)


def sync_registry_from_tree(tree: node.BTree) -> None:
    reg = {"pages": {}}
    if tree.root:
        _walk_tree_pages(tree.root, "root", reg, 1)
    save_registry(reg)


def _walk_tree_pages(n: dict, pid: str, reg: dict, generation: int) -> None:
    if node.is_leaf(n):
        body = f"leaf:{node.entries(n)!r}"
    else:
        keys, _, _ = node.internal_parts(n)
        body = f"internal:{keys!r}"
    hk = node.subtree_max_key(n)
    header = {"page_id": pid, "generation": generation, "high_key": hk}
    cs = checksum.page_checksum(header, body.encode("utf-8"))
    reg["pages"][pid] = {"header": header, "body": body, "checksum": cs}
    if not node.is_leaf(n):
        _, children, _ = node.internal_parts(n)
        for i, child in enumerate(children):
            _walk_tree_pages(child, f"{pid}-{i}", reg, generation)
