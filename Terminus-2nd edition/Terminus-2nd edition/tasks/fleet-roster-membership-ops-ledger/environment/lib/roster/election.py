from __future__ import annotations


def apply_election(current_term: int, leader_id: str, entry: dict) -> tuple[int, str]:
    # BUG: runs for any entry kind; uses >= instead of election-only rules
    node = entry.get("payload", {}).get("node_id", "")
    role = entry.get("payload", {}).get("role", "")
    term = int(entry.get("term", 0))
    if term >= current_term:
        current_term = term
        if role == "leader":
            leader_id = str(node)
    return current_term, leader_id
