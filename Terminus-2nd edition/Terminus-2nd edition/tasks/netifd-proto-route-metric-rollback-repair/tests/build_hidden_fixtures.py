#!/usr/bin/env python3
"""Generate hidden verifier fixtures at test runtime (not baked into agent image)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("TB3_FIXTURES_DIR", "/opt/verifier-fixtures/netifd"))
SCENARIOS = ROOT / "scenarios"

HIDDEN = {
    "reload-metric-trap.json": {
        "iface": "veth9",
        "config_metric": 80,
        "kernel_metric_bonus": 99,
        "routes": [{"dst": "0.0.0.0/0", "via": "203.0.113.9"}],
        "hotplug": [],
        "rules": [{"priority": 80, "from": "all", "lookup": "main"}],
    }
}


def main() -> None:
    SCENARIOS.mkdir(parents=True, exist_ok=True)
    catalog = {"scenarios": [{"name": k[:-5], "file": k} for k in HIDDEN]}
    (ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    for name, body in HIDDEN.items():
        (SCENARIOS / name).write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
