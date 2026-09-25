from __future__ import annotations

import json
from pathlib import Path

from sled import btree, node, replay
from sled.state import load_staging, save_staging


def parse_batch_file(path: Path) -> list[dict]:
    ops: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row["op"] not in ("put", "delete"):
            raise ValueError(f"unknown op: {row['op']}")
        ops.append(row)
    return ops


def apply_batch_file(table: str, path: Path) -> None:
    ops = parse_batch_file(path)
    staging = load_staging()
    tree = staging.tables.setdefault(table, node.BTree())
    puts = replay.collapse_puts(ops)
    for key, value in sorted(puts, key=lambda x: x[0]):
        replay.append_put(tree, key, value)
    for op in ops:
        if op["op"] == "delete":
            btree.delete(tree, op["key"])
    save_staging(staging)


def delete_key(table: str, key: str) -> None:
    staging = load_staging()
    tree = staging.tables.setdefault(table, node.BTree())
    btree.delete(tree, key)
    save_staging(staging)
