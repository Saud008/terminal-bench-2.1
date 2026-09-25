from __future__ import annotations

import json
from pathlib import Path

from sled import btree, node
from sled.config import APPLIED_PATH


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
    from sled.state import load_committed, save_committed

    committed = load_committed()
    tree = committed.tables.get(table, node.BTree())
    run_path = Path("/app/state/journal_replay_run.json")
    run = 0
    if run_path.is_file():
        run = int(json.loads(run_path.read_text(encoding="utf-8")).get("run", 0))
    run += 1
    run_path.write_text(json.dumps({"run": run}), encoding="utf-8")
    applied = 0
    for line in journal_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        kind = entry.get("kind")
        if kind == "ParentPivot":
            pivot = f"journal-run-{run}"
            btree.insert(tree, pivot, "split-marker")
            applied += 1
        elif kind == "RightPage":
            body = entry.get("body", "")
            if "duplicate" in body:
                btree.insert(tree, f"dup-{run}", body)
                applied += 1
    committed.tables[table] = tree
    save_committed(committed)
    return applied
