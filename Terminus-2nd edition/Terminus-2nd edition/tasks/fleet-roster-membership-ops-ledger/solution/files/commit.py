from __future__ import annotations


def apply_commit(commit_index: int, entry: dict) -> int:
    if entry.get("kind") == "commit":
        ci = int(entry["payload"]["commit_index"])
        commit_index = max(commit_index, ci)
    return commit_index
