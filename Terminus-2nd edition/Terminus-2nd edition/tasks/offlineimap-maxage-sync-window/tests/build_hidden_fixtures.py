#!/usr/bin/env python3
"""Generate hidden verifier fixtures at test runtime (not baked into agent image)."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

APP = Path("/app")
BASIC = APP / "fixtures" / "scenarios" / "basic-inbox"
WORK = APP / "fixtures" / "scenarios" / "work-exclude"
OUT_ROOT = Path(os.environ.get("TB3_FIXTURES_DIR", "/opt/verifier-fixtures/offlineimap"))
VALIDITY_DIR = OUT_ROOT / "scenarios" / "validity-bump"
EXCLUDE_ONLY_DIR = OUT_ROOT / "scenarios" / "exclude-only"


def _write_rules(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_validity_bump() -> None:
    if VALIDITY_DIR.exists():
        shutil.rmtree(VALIDITY_DIR)
    VALIDITY_DIR.mkdir(parents=True)
    (VALIDITY_DIR / "maildir").mkdir()
    shutil.copy2(BASIC / "messages.tsv", VALIDITY_DIR / "messages.tsv")
    shutil.copy2(BASIC / "folder.rules", VALIDITY_DIR / "folder.rules")
    meta = json.loads((BASIC / "imap-meta.json").read_text(encoding="utf-8"))
    meta["folders"][0]["uidvalidity"] = 99
    (VALIDITY_DIR / "imap-meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def build_exclude_only() -> None:
    if EXCLUDE_ONLY_DIR.exists():
        shutil.rmtree(EXCLUDE_ONLY_DIR)
    EXCLUDE_ONLY_DIR.mkdir(parents=True)
    (EXCLUDE_ONLY_DIR / "maildir").mkdir()
    shutil.copy2(WORK / "messages.tsv", EXCLUDE_ONLY_DIR / "messages.tsv")
    shutil.copy2(WORK / "imap-meta.json", EXCLUDE_ONLY_DIR / "imap-meta.json")
    _write_rules(EXCLUDE_ONLY_DIR / "folder.rules", ["exclude Work/Archive"])


def build() -> None:
    build_validity_bump()
    build_exclude_only()
    verifier_catalog = {
        "scenarios": [
            {
                "name": "validity-bump",
                "kind": "uidvalidity-reset",
                "reference_epoch": 1_700_020_000,
                "maxage_sec": 86400,
                "tz_offset": 0,
            },
            {
                "name": "exclude-only",
                "kind": "exclude-filter-only",
                "reference_epoch": 1_700_010_000,
                "maxage_sec": 604800,
                "tz_offset": 0,
            },
        ]
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "catalog.json").write_text(
        json.dumps(verifier_catalog, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
