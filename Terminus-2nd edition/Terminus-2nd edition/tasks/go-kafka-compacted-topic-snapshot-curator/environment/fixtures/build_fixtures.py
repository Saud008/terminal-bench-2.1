"""Fixture metadata builder - uses hashlib and unicodedata per verifier-refmath-contract.md."""
from __future__ import annotations

import hashlib
import json
import os
import unicodedata
from pathlib import Path


def scenario_slug(name: str) -> str:
    return unicodedata.normalize("NFC", name.strip())


def catalog_digest(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    root = Path("/app/fixtures")
    hidden = os.environ.get("KCOMPACT_HIDDEN_ROOT")
    if hidden:
        root = Path(hidden)
    scenarios = sorted(scenario_slug(p.name) for p in (root / "compact-logs").iterdir() if p.is_dir())
    catalog = {"root": str(root), "scenarios": scenarios}
    catalog["catalog_digest"] = catalog_digest(catalog)
    out = root / "catalog.json"
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
