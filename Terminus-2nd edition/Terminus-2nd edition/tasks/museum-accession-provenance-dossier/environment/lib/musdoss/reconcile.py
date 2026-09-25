from __future__ import annotations


def duplicate_conflicts(objects: list[dict[str, str]]) -> list[dict[str, list[str] | str]]:
    by_title: dict[str, list[str]] = {}
    for obj in objects:
        by_title.setdefault(obj["title"], []).append(obj["accession_id"])
    out: list[dict[str, list[str] | str]] = []
    for title, ids in by_title.items():
        if len(ids) < 2:
            continue
        out.append(
            {
                "primary_accession_id": title,
                "shadow_accession_ids": sorted(ids),
            }
        )
    return out
