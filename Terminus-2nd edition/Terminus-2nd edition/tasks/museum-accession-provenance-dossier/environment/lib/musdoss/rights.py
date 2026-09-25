from __future__ import annotations


def active_restrictions(
    rows: list[dict[str, str | int]], focus_id: str, as_of: str
) -> list[dict[str, str | int]]:
    _ = as_of
    by_level: dict[str, dict[str, str | int]] = {}
    for row in rows:
        if row["accession_id"] != focus_id:
            continue
        level = str(row["level"])
        cur = by_level.get(level)
        if cur is None or int(row["precedence"]) > int(cur["precedence"]):
            by_level[level] = row
    out = [{"level": row["level"], "precedence": row["precedence"]} for row in by_level.values()]
    return sorted(out, key=lambda item: str(item["level"]))
