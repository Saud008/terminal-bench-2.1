#!/usr/bin/env python3
"""Build maildir manifests and IMAP metadata for bundled fixtures."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
SCENARIOS = FIX / "scenarios"


def write_tsv(path: Path, rows: list[tuple[str, int, int, int]]) -> None:
    lines = ["folder\tinternal_date\tsize_bytes\tuid"]
    for folder, idate, size, uid in rows:
        lines.append(f"{folder}\t{idate}\t{size}\t{uid}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_meta(path: Path, account: str, folders: list[dict]) -> None:
    path.write_text(
        json.dumps({"account": account, "folders": folders}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_rules(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_all() -> None:
    SCENARIOS.mkdir(parents=True, exist_ok=True)

    base = SCENARIOS / "basic-inbox"
    base.mkdir(parents=True, exist_ok=True)
    (base / "maildir").mkdir(exist_ok=True)
    write_tsv(
        base / "messages.tsv",
        [
            ("INBOX", 1_699_933_700, 400, 3),
            ("INBOX", 1_700_000_000, 1200, 1),
            ("INBOX", 1_700_010_000, 800, 2),
        ],
    )
    write_meta(
        base / "imap-meta.json",
        "user@example.com",
        [{"name": "INBOX", "uidvalidity": 42, "uidnext": 10}],
    )
    write_rules(base / "folder.rules", ["include INBOX"])

    work = SCENARIOS / "work-exclude"
    work.mkdir(parents=True, exist_ok=True)
    (work / "maildir").mkdir(exist_ok=True)
    write_tsv(
        work / "messages.tsv",
        [
            ("INBOX", 1_700_000_100, 500, 1),
            ("Work/Active", 1_700_000_200, 900, 2),
            ("Work/Archive", 1_700_000_300, 1500, 3),
        ],
    )
    write_meta(
        work / "imap-meta.json",
        "ops@corp.example",
        [
            {"name": "INBOX", "uidvalidity": 7, "uidnext": 5},
            {"name": "Work/Active", "uidvalidity": 8, "uidnext": 5},
            {"name": "Work/Archive", "uidvalidity": 9, "uidnext": 5},
        ],
    )
    write_rules(
        work / "folder.rules",
        ["include INBOX", "include Work/*", "exclude Work/Archive"],
    )

    tz = SCENARIOS / "tz-offset"
    tz.mkdir(parents=True, exist_ok=True)
    (tz / "maildir").mkdir(exist_ok=True)
    write_tsv(
        tz / "messages.tsv",
        [
            ("INBOX", 1_700_003_000, 100, 1),
            ("INBOX", 1_700_002_000, 200, 2),
        ],
    )
    write_meta(
        tz / "imap-meta.json",
        "tz@example.com",
        [{"name": "INBOX", "uidvalidity": 3, "uidnext": 4}],
    )
    write_rules(tz / "folder.rules", ["include INBOX"])

    catalog = {
        "scenarios": [
            {
                "name": "basic-inbox",
                "reference_epoch": 1_700_020_000,
                "maxage_sec": 86400,
                "tz_offset": 0,
            },
            {
                "name": "work-exclude",
                "reference_epoch": 1_700_010_000,
                "maxage_sec": 604800,
                "tz_offset": 0,
            },
            {
                "name": "tz-offset",
                "reference_epoch": 1_700_000_000,
                "maxage_sec": 1200,
                "tz_offset": 60,
            },
        ]
    }
    (FIX / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_all()
