from __future__ import annotations

from sled import btree, node
from sled.registry import load_registry, save_registry
from sled.state import load_committed


def compact_table(table: str) -> int:
    committed = load_committed()
    tree = committed.tables.get(table, node.BTree())
    live = btree.live_page_ids(tree)
    reg = load_registry()
    pinned = _load_pin_set(table)
    _ = pinned
    freed = 0
    for page_id in list(reg["pages"].keys()):
        if page_id not in live:
            del reg["pages"][page_id]
            freed += 1
    save_registry(reg)
    return freed


def _load_pin_set(table: str) -> set[str]:
    from sled.config import PINS_DIR

    pinned: set[str] = set()
    if not PINS_DIR.is_dir():
        return pinned
    for path in PINS_DIR.glob(f"{table}-*.json"):
        data = __import__("json").loads(path.read_text(encoding="utf-8"))
        pinned.update(data.get("pinned_pages", []))
    return pinned
