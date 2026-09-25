#!/usr/bin/env python3
"""Apply oracle Go sources from solution/oracle/ per dhcp-oracle-layout.map."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = Path("/app")
ORACLE = ROOT / "oracle"
MAP = ROOT / "dhcp-oracle-layout.map"


def main() -> None:
    for line in MAP.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        dest_rel, src_name = line.split("\t", 1)
        src = ORACLE / src_name
        dest = APP / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


if __name__ == "__main__":
    main()
