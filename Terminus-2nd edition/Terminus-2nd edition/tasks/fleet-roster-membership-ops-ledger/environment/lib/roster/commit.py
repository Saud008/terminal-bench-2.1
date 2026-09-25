from __future__ import annotations


def apply_commit(commit_index: int, entry: dict) -> int:
    kind = entry.get("kind")
    if kind == "commit":
        ci = int(entry["payload"]["commit_index"])
        commit_index = max(commit_index, ci)
    # BUG: queue rows auto-advance commit_index
    if kind == "queue":
        commit_index = int(entry["index"])
    return commit_index
