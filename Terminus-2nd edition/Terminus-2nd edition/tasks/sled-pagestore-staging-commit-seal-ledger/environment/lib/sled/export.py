from __future__ import annotations

import json
from pathlib import Path

from sled import btree, node
from sled.state import load_committed


def export_table(table: str, out: Path) -> None:
    rows = scan_committed_table(table)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def export_range(table: str, start: str, end: str, out: Path) -> None:
    rows = scan_range(table, start, end)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def scan_committed_table(table: str) -> list[dict[str, str]]:
    committed = load_committed()
    tree = committed.tables.get(table, node.BTree())
    return [{"key": k, "value": v} for k, v in btree.ordered_entries(tree)]


def scan_range(table: str, start: str, end: str) -> list[dict[str, str]]:
    committed = load_committed()
    tree = committed.tables.get(table, node.BTree())
    rows: list[dict[str, str]] = []
    if tree.root:
        _collect_range(tree.root, start, end, rows)
    rows.sort(key=lambda r: r["key"])
    dedup: dict[str, str] = {}
    for row in rows:
        dedup[row["key"]] = row["value"]
    return [{"key": k, "value": v} for k, v in dedup.items()]


def _collect_range(n: dict, start: str, end: str, out: list[dict[str, str]]) -> None:
    if node.is_leaf(n):
        for e in node.entries(n):
            if start <= e[0] <= end:
                out.append({"key": e[0], "value": e[1]})
    else:
        _, children, high_key = node.internal_parts(n)
        if high_key is not None and high_key < start:
            return
        for child in children:
            _collect_range(child, start, end, out)
