#!/usr/bin/env python3
"""Build fixture integrity manifest at image build time."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("/app/fixtures")
OUT = ROOT / "manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    entries: dict[str, str] = {}
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            rel = path.relative_to(ROOT).as_posix()
            entries[rel] = sha256(path)
    OUT.write_text(json.dumps({"files": entries}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
