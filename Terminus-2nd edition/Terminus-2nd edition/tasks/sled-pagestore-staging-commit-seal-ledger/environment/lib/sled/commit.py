from __future__ import annotations

import json

from sled import barrier, btree
from sled.config import SNAPSHOT_PATH
from sled.registry import sync_registry_from_tree
from sled.split_log import record_splits_for_table
from sled.state import load_committed, load_staging, save_committed, save_staging


def write_snapshot(table: str, height: int, leaves: int, keys: int) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(
            {
                "table": table,
                "root_height": height,
                "leaf_count": leaves,
                "key_count": keys,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def commit_table(table: str) -> None:
    staging = load_staging()
    if table not in staging.tables:
        return
    tree = staging.tables[table]
    height = tree.height
    leaves = btree.leaf_count(tree)
    keys = btree.unique_key_count(tree)
    barrier.run_commit_barrier(table, height, tree)
    split_events = max(0, leaves - 1)
    if split_events > 0:
        record_splits_for_table(table, split_events)
    sync_registry_from_tree(tree)
    committed = load_committed()
    committed.tables[table] = tree
    save_committed(committed)
    write_snapshot(table, height, leaves, keys)
    del staging.tables[table]
    save_staging(staging)
