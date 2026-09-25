#!/usr/bin/env python3
"""Build /opt/verifier-fixtures/wal hidden database pairs for verifier-only tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_seed_wal import build_pair  # noqa: E402


def main() -> None:
    out = Path("/opt/verifier-fixtures/wal/hidden")
    out.mkdir(parents=True, exist_ok=True)
    db = out / "ledger.db"
    build_pair(
        db,
        [("TB3-HIDDEN-A", 9), ("TB3-HIDDEN-B", 4)],
        salt1=0xA1B2C3D4,
        salt2=0x11223344,
        page_nos=[1, 2],
    )
    print(f"built hidden fixture at {db}")


if __name__ == "__main__":
    main()
