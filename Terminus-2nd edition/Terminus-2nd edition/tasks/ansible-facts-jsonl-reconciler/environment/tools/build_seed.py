#!/usr/bin/env python3
"""Build bundled seed Ansible facts JSONL fixtures for the image."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def record(
    inventory_uuid: str,
    hostname: str,
    collected_at: str,
    facts: dict,
) -> dict:
    return {
        "inventory_uuid": inventory_uuid,
        "hostname": hostname,
        "collected_at": collected_at,
        "facts": facts,
    }


def build_seed(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    lines = [
        record(
            "11111111-1111-4111-8111-111111111111",
            "web-01.example.com",
            "2024-06-15T09:00:00Z",
            {"ansible_os_family": "Debian", "ansible_memtotal_mb": 4096},
        ),
        record(
            "22222222-2222-4222-8222-222222222222",
            "web-01.example.com",
            "2024-06-15T09:30:00Z",
            {"ansible_os_family": "RedHat", "ansible_memtotal_mb": 16384},
        ),
        record(
            "11111111-1111-4111-8111-111111111111",
            "web-01.example.com",
            "2024-06-15T10:00:00Z",
            {
                "ansible_os_family": "Debian",
                "ansible_memtotal_mb": 8192,
                "ansible_processor_cores": 4,
            },
        ),
    ]
    out = dest / "facts.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for obj in lines:
            fh.write(json.dumps(obj, separators=(",", ":"), sort_keys=True))
            fh.write("\n")


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/app/fixtures/seed")
    if out.exists():
        shutil.rmtree(out)
    build_seed(out)


if __name__ == "__main__":
    main()
