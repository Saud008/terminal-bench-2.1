"""Thin bridge so impose flow can write staging without importing staging package cycles."""

from __future__ import annotations

from pathlib import Path

from staging.snapshot import write_snapshot


def write_staging_snapshot(seed: int, set_name: str, mark_count: int) -> Path:
    return write_snapshot(seed, set_name, mark_count)
