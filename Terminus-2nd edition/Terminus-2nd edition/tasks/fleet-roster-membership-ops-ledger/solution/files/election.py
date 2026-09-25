from __future__ import annotations


def apply_election(current_term: int, leader_id: str, entry: dict) -> tuple[int, str]:
    if entry.get("kind") != "election":
        return current_term, leader_id
    node = entry["payload"]["node_id"]
    role = entry["payload"]["role"]
    term = int(entry["term"])
    if term > current_term:
        current_term = term
        if role == "leader":
            leader_id = str(node)
    elif term == current_term and role == "leader":
        leader_id = str(node)
    return current_term, leader_id
