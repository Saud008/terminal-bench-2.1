#!/usr/bin/env python3
"""Materialize scenario JSON with deterministic pseudo-random ISINs and rates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("/app/fixtures/scenarios")
HIDDEN = Path("/opt/verifier-fixtures/bondacc/scenarios")


def mutate(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    seed = int(hashlib.sha256(data["scenario"].encode()).hexdigest()[:8], 16)
    bps = 300 + (seed % 200)
    for bond in data.get("bonds", []):
        bond["coupon_bps"] = bps
        isin_seed = hashlib.sha256(f"{data['scenario']}-{bps}".encode()).hexdigest()
        bond["isin"] = "US" + isin_seed[:10].upper()
        for trade in data.get("trades", []):
            trade["isin"] = bond["isin"]
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for d in (ROOT, HIDDEN):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.json")):
            mutate(p)


if __name__ == "__main__":
    main()
