#!/usr/bin/env python3
"""Fixture catalog builder for xsnapctl scenarios."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def main() -> None:
    root = Path("/app/fixtures")
    hidden = os.environ.get("XSNAP_HIDDEN_ROOT")
    if hidden:
        root = Path(hidden)
    scenarios = sorted(p.name for p in (root / "scenarios").iterdir() if p.is_dir())
    catalog = {
        "root": str(root),
        "scenarios": scenarios,
        "catalog_sha256": hashlib.sha256(json.dumps(scenarios).encode()).hexdigest(),
    }
    out = root / "catalog.json"
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

