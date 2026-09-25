from __future__ import annotations

import json

from sled.config import JOURNAL_PATH
from sled.registry import persist_page


def append_split_event(
    table: str,
    split_seq: int,
    page_id: str,
    pivot: str,
    generation: int,
    body: str,
) -> None:
    _append_entry(
        {
            "kind": "ParentPivot",
            "table": table,
            "split_seq": split_seq,
            "pivot": pivot,
        }
    )
    persist_page(
        page_id,
        {"page_id": page_id, "generation": generation, "high_key": None},
        body,
    )
    _append_entry(
        {
            "kind": "RightPage",
            "table": table,
            "split_seq": split_seq,
            "page_id": page_id,
            "generation": generation,
            "body": body,
        }
    )


def _append_entry(entry: dict) -> None:
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def record_splits_for_table(table: str, split_count: int) -> None:
    for seq in range(1, split_count + 1):
        page_id = f"{table}-split-{seq}-right"
        append_split_event(table, seq, page_id, f"pivot-{seq}", 1, f"right-body-{seq}")
