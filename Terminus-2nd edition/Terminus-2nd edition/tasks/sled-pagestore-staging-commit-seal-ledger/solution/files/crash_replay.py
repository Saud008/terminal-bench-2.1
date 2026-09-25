from __future__ import annotations

import json
from pathlib import Path

from sled import btree, node
from sled.config import APPLIED_PATH
from sled.state import load_committed, save_committed


def _load_applied() -> set[int]:
    if not APPLIED_PATH.is_file():
        return set()
    data = json.loads(APPLIED_PATH.read_text(encoding="utf-8"))
    return set(data.get("split_seq", []))


def _save_applied(seqs: set[int]) -> None:
    APPLIED_PATH.parent.mkdir(parents=True, exist_ok=True)
    APPLIED_PATH.write_text(
        json.dumps({"split_seq": sorted(seqs)}, indent=2), encoding="utf-8"
    )


def replay_crash_journal(table: str, journal_path: Path) -> int:
    committed = load_committed()
    tree = committed.tables.get(table, node.BTree())
    applied_state = _load_applied()
    applied = 0
    for line in journal_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        kind = entry.get("kind")
        split_seq = int(entry.get("split_seq", 0))
        if split_seq in applied_state:
            continue
        if kind == "ParentPivot":
            btree.insert(tree, entry["pivot"], "split-marker")
            applied_state.add(split_seq)
            applied += 1
        elif kind == "RightPage":
            body = entry.get("body", "")
            if "duplicate" in body:
                btree.insert(tree, f"dup-{split_seq}", body)
                applied_state.add(split_seq)
                applied += 1
    _save_applied(applied_state)
    committed.tables[table] = tree
    save_committed(committed)
    return applied
