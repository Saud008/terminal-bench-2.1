"""Small helpers for RPM attestation key ordering."""

from __future__ import annotations


def sorted_module_names(rows: list[dict]) -> list[str]:
    return sorted(row.get("module", "") for row in rows)
