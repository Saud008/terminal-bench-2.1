"""Duplicate version graph helpers for catalog previews."""

from __future__ import annotations


def group_versions(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in rows:
        out.setdefault(row["name"], []).append(row["version"])
    return out
