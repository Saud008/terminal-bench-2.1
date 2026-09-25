from __future__ import annotations

from sled import barrier, btree, node
from sled.state import load_committed


def walk_table(table: str) -> dict:
    committed = load_committed()
    tree = committed.tables.get(table, node.BTree())
    record = barrier.load_commit_record()
    height_flag = bool(record and record.get("height_recorded_before_child_fsync"))
    return {
        "table": table,
        "root_height": tree.height,
        "leaf_count": btree.leaf_count(tree),
        "key_count": btree.unique_key_count(tree),
        "physical_entry_count": btree.physical_entry_count(tree),
        "height_recorded_before_child_fsync": height_flag,
    }
