from __future__ import annotations


def detect_conflicts(loans: list[dict[str, str]], focus_id: str, as_of: str) -> list[dict[str, str]]:
    _ = as_of
    out: list[dict[str, str]] = []
    for loan in loans:
        if loan["accession_id"] == focus_id:
            continue
        out.append({"accession_id": loan["accession_id"], "reason": "ignored"})
    return out
