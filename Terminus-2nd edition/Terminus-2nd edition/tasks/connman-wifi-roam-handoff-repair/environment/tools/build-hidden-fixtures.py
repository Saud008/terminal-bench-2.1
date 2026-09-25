#!/usr/bin/env python3
"""Build hidden roam scenarios for verifier-only fixtures."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

APP = Path("/app")
OUT = Path("/opt/verifier-fixtures/roam-scenarios")
OUT.mkdir(parents=True, exist_ok=True)

HIDDEN = {
    "tb3-consent-granted": {
        "scenario_id": "tb3-consent-granted",
        "current_bss": {"ssid": "Old", "bssid": "aa:tb:01", "gateway": "192.168.77.1"},
        "target_bss": {"ssid": "HiddenOK", "bssid": "bb:tb:02", "gateway": "10.77.0.1"},
        "disconnect_delay_ms": 4,
        "scan": {
            "required_bssids": ["bb:tb:02"],
            "events": [{"type": "full", "bssids_seen": ["bb:tb:02"], "coverage": 1.0}],
        },
        "services": [
            {"ssid": "Visible", "security": "wpa2", "signal": -60, "hidden": False, "preference": 4}
        ],
        "hidden_candidate": {
            "ssid": "HiddenOK",
            "security": "wpa3",
            "signal": -38,
            "hidden": True,
            "preference": 22,
        },
        "user_consent_hidden": True,
    },
    "tb3-partial-only": {
        "scenario_id": "tb3-partial-only",
        "current_bss": {"ssid": "A", "bssid": "aa:tb:03", "gateway": "192.168.3.1"},
        "target_bss": {"ssid": "B", "bssid": "cc:tb:04", "gateway": "10.3.0.1"},
        "disconnect_delay_ms": 3,
        "scan": {
            "required_bssids": ["cc:tb:04"],
            "events": [{"type": "partial", "bssids_seen": ["cc:tb:04"], "coverage": 0.9}],
        },
        "services": [
            {"ssid": "B", "security": "wpa2", "signal": -50, "hidden": False, "preference": 9}
        ],
        "hidden_candidate": None,
        "user_consent_hidden": False,
    },
}

for name, payload in HIDDEN.items():
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

# seed bundled catalog copies for integrity checks
bundled = APP / "fixtures" / "scenarios"
for src in bundled.glob("*.json"):
    shutil.copy2(src, OUT / src.name)

print(f"built hidden roam fixtures under {OUT}")
