from __future__ import annotations


def filter_after_snapshot(entries: list[dict], snap: dict) -> list[dict]:
    cutoff = int(snap["last_included_index"])
    return [e for e in entries if int(e["index"]) > cutoff]


def load_baseline(snap: dict) -> tuple[dict[str, int], list[str], int]:
    qs = {k: int(v) for k, v in snap.get("queue_states", {}).items()}
    mem = list(snap.get("membership", []))
    return qs, mem, int(snap["commit_index"])
