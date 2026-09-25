#!/usr/bin/env python3
"""Write SHA256 manifest for fixture tables."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("/app/fixtures")
TABLES = ROOT / "tables"
manifest: dict[str, str] = {}

for path in sorted(TABLES.glob("*.md")):
    rel = f"tables/{path.name}"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest[rel] = digest

(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
