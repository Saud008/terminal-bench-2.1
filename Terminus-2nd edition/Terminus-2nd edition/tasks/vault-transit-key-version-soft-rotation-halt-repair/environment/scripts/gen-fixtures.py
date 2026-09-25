#!/usr/bin/env python3
"""Generate transit policy fixtures with per-scenario fields."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "fixtures" / "policies"

POLICIES = {
    "orion-min3.json": {
        "type": "aes256-gcm96",
        "min_decryption_version": 3,
        "deletion_allowed": False,
        "convergent_encryption": False,
        "exportable": False,
        "soft_rotation_halt_after_version": 0,
        "rotation_epoch": "2024-11-02T08:15:00Z",
    },
    "kappa-batch.json": {
        "type": "aes256-gcm96",
        "min_decryption_version": 1,
        "deletion_allowed": False,
        "convergent_encryption": False,
        "exportable": False,
        "soft_rotation_halt_after_version": 0,
        "rotation_epoch": "2024-11-03T14:22:00Z",
    },
    "kappa-delete-allow.json": {
        "type": "aes256-gcm96",
        "min_decryption_version": 1,
        "deletion_allowed": True,
        "convergent_encryption": False,
        "exportable": False,
        "soft_rotation_halt_after_version": 0,
        "rotation_epoch": "2024-11-03T14:23:00Z",
    },
    "sigma-halt.json": {
        "type": "aes256-gcm96",
        "min_decryption_version": 1,
        "deletion_allowed": False,
        "convergent_encryption": True,
        "exportable": False,
        "soft_rotation_halt_after_version": 0,
        "rotation_epoch": "2024-11-04T09:40:00Z",
    },
}

POLICY_DIR.mkdir(parents=True, exist_ok=True)
for name, body in POLICIES.items():
    (POLICY_DIR / name).write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

print(f"wrote {len(POLICIES)} policies to {POLICY_DIR}")
