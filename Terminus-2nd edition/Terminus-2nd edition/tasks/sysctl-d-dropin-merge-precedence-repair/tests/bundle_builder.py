"""Build ephemeral sysctl bundle trees for verifier-only anti-cheat checks."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path


def procedural_tree(seed: str) -> Path:
    """Seed-derived bundle under /tmp; ordering and winners depend on seed."""
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    token = digest[:8]
    root = Path(tempfile.mkdtemp(prefix=f"proc-{token}-"))
    (root / "sysctl.conf").write_text(
        f"proc.base.key = {token}\nshared.proc.key = base-{token}\n",
        encoding="utf-8",
    )
    drop_dir = root / "sysctl.d"
    drop_dir.mkdir()
    (drop_dir / "10-a.conf").write_text(f"shared.proc.key = drop-a-{token}\n", encoding="utf-8")
    (drop_dir / "20-b.conf").write_text(f"shared.proc.key = drop-b-{token}\n", encoding="utf-8")
    manifest = {
        "main": "sysctl.conf",
        "drop_ins": ["sysctl.d/10-a.conf", "sysctl.d/20-b.conf"],
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return root
