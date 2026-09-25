from __future__ import annotations

import json
from pathlib import Path

from roster.seal import compute_membership_seal


def export_ledger(st: dict, ledger_path: str, seal_path: str) -> None:
    rows = []
    for qid, msgs in st["queue_states"].items():
        if qid == "":
            continue
        rows.append(
            {
                "queue_id": qid,
                "messages": msgs,
                "leader_id": st["leader_id"],
                "term": st["current_term"],
                "commit_index": st["commit_index"],
                "replicas": sorted(st["membership"]),
            }
        )
    rows.sort(key=lambda r: r["queue_id"])
    Path(ledger_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(ledger_path).open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(row, separators=(",", ":")) + "\n" for row in rows)
    seal = {
        "raft_seal": compute_membership_seal(st),
        "membership_epoch": st["current_term"],
        "export_row_count": len(rows),
    }
    Path(seal_path).write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
