from __future__ import annotations

from sled import btree, node
from sled.pin import load_pin_set
from sled.registry import load_registry, save_registry
from sled.state import load_committed


def compact_table(table: str) -> int:
    committed = load_committed()
    tree = committed.tables.get(table, node.BTree())
    live = btree.live_page_ids(tree)
    pinned = load_pin_set(table)
    reg = load_registry()
    freed = 0
    for page_id in list(reg["pages"].keys()):
        if page_id not in live and page_id not in pinned:
            del reg["pages"][page_id]
            freed += 1
    save_registry(reg)
    return freed
