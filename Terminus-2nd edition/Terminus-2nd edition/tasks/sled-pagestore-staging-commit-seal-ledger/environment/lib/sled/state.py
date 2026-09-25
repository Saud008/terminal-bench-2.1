from __future__ import annotations

import json
from dataclasses import dataclass, field

from sled import node
from sled.config import COMMITTED_PATH, STAGING_PATH


@dataclass
class TableState:
    tables: dict[str, node.BTree] = field(default_factory=dict)


def _tree_to_json(tree: node.BTree) -> dict:
    return {"root": tree.root, "height": tree.height}


def _tree_from_json(data: dict) -> node.BTree:
    return node.BTree(root=data.get("root"), height=int(data.get("height", 0)))


def load_committed() -> TableState:
    if not COMMITTED_PATH.is_file():
        return TableState()
    raw = json.loads(COMMITTED_PATH.read_text(encoding="utf-8"))
    state = TableState()
    for name, payload in raw.get("tables", {}).items():
        state.tables[name] = _tree_from_json(payload)
    return state


def save_committed(state: TableState) -> None:
    COMMITTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tables": {name: _tree_to_json(tree) for name, tree in state.tables.items()}
    }
    COMMITTED_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_staging() -> TableState:
    if not STAGING_PATH.is_file():
        return TableState()
    raw = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    state = TableState()
    for name, payload in raw.get("tables", {}).items():
        state.tables[name] = _tree_from_json(payload)
    return state


def save_staging(state: TableState) -> None:
    STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tables": {name: _tree_to_json(tree) for name, tree in state.tables.items()}
    }
    STAGING_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
