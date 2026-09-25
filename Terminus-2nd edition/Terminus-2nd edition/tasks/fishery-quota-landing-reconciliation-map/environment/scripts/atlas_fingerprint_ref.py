"""Atlas fingerprint reference — mirrors pytest hashlib.sha256 contract."""

from __future__ import annotations

import hashlib
import json


def atlas_fingerprint(species_rows: list, landing_audit: list) -> str:
    body = {"species_rows": species_rows, "landing_audit": landing_audit}
    return hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest()
