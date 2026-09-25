"""Build hidden tmpfiles scenarios for verifier anti-cheat."""

from __future__ import annotations

import json
from pathlib import Path


def build_hidden_age_trap(base: Path) -> Path:
    """Hidden fixture: young btime must block removal when mtime is stale."""
    scen = base / "hidden-age-trap"
    scen.mkdir(parents=True, exist_ok=True)
    tree = {
        "paths": {
            "/var/tmp/hidden/edge.log": {
                "kind": "f",
                "mode": "0644",
                "user": "root",
                "group": "root",
                "atime": 500,
                "btime": 9800,
                "mtime": 500,
            }
        }
    }
    (scen / "tree.json").write_text(json.dumps(tree, indent=2), encoding="utf-8")
    (scen / "rules.conf").write_text("r! /var/tmp/hidden/*.log 3600\n", encoding="utf-8")
    return scen
