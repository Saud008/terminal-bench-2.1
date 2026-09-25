from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_canonical_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()
