from __future__ import annotations


def apply_config(membership: list[str], epoch_term: int, entry: dict) -> tuple[list[str], int]:
    if entry.get("kind") != "config":
        return membership, epoch_term
    term = int(entry["term"])
    if term < epoch_term:
        return membership, epoch_term
    epoch_term = term
    op = entry["payload"]["op"]
    node = entry["payload"]["node_id"]
    mem = list(membership)
    if op == "add_voter" and node not in mem:
        mem.append(node)
    if op == "remove_voter" and node in mem:
        mem.remove(node)
    mem.sort()
    return mem, epoch_term
