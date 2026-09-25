"""Independent policy file reader for verifier checks."""

from __future__ import annotations

import json
from pathlib import Path


def read_policy(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    min_ver = int(data.get("min_decryption_version", 1))
    if min_ver < 1:
        min_ver = 1
    return {
        "type": data.get("type") or "aes256-gcm96",
        "min_decryption_version": min_ver,
        "deletion_allowed": bool(data.get("deletion_allowed", False)),
        "convergent_encryption": bool(data.get("convergent_encryption", False)),
        "exportable": bool(data.get("exportable", False)),
        "soft_rotation_halt_after_version": int(
            data.get("soft_rotation_halt_after_version", 0)
        ),
    }
