#!/usr/bin/env python3
"""Fragment merge for systemd timer bundles."""

from __future__ import annotations

from pathlib import Path


def parse_ini_sections(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, {})
            continue
        if "=" in line and current:
            key, val = line.split("=", 1)
            sections[current][key.strip()] = val.strip()
    return sections


def merge_timer_bundle(bundle: Path, timer_name: str) -> dict[str, str]:
    timer: dict[str, str] = {}
    drop_dir = bundle / f"{timer_name}.timer.d"
    if drop_dir.is_dir():
        for frag in sorted(drop_dir.glob("*.conf"), reverse=True):
            timer.update(parse_ini_sections(frag.read_text(encoding="utf-8")).get("Timer", {}))
    base_file = bundle / f"{timer_name}.timer"
    if base_file.is_file():
        timer.update(parse_ini_sections(base_file.read_text(encoding="utf-8")).get("Timer", {}))
    return timer
