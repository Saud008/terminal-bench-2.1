from __future__ import annotations


def duplicate_conflicts(objects: list[dict[str, str]]) -> list[dict[str, list[str] | str]]:
    by_id: dict[str, list[str]] = {}
    for obj in objects:
        by_id.setdefault(obj["accession_id"], []).append(obj["accession_id"])
    out: list[dict[str, list[str] | str]] = []
    for accession_id, ids in by_id.items():
        if len(ids) < 2:
            continue
        out.append(
            {
                "primary_accession_id": accession_id,
                "shadow_accession_ids": sorted(ids),
            }
        )
    return sorted(out, key=lambda item: str(item["primary_accession_id"]))
