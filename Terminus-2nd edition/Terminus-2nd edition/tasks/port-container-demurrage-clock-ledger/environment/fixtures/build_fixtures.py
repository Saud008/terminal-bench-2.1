#!/usr/bin/env python3
"""Validate scenario JSON catalog and emit scenario_catalog.json."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN_ROOT = Path(os.environ.get("DEMUR_HIDDEN_ROOT", "")) if os.environ.get("DEMUR_HIDDEN_ROOT") else None


def catalog_fingerprint(names: list[str]) -> str:
    payload = ",".join(names).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def sqlite_catalog_probe() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE probe (name TEXT)")
    conn.close()


def collect_scenarios(base: Path) -> list[str]:
    scen_dir = base / "scenarios"
    if not scen_dir.is_dir():
        return []
    return sorted(p.stem for p in scen_dir.glob("*.json"))


def main() -> None:
    bundled = collect_scenarios(ROOT)
    sqlite_catalog_probe()
    catalog = {
        "bundled": bundled,
        "engine": "demurctl",
        "catalog_fp": catalog_fingerprint(bundled),
    }
    if HIDDEN_ROOT and HIDDEN_ROOT.is_dir():
        catalog["hidden"] = collect_scenarios(HIDDEN_ROOT)
    out = ROOT / "scenario_catalog.json"
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    for name in bundled:
        path = ROOT / "scenarios" / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("scenario_id") == name, f"scenario_id mismatch in {path}"
    print(f"demurctl fixtures ok: {len(bundled)} bundled scenarios")


if __name__ == "__main__":
    main()
