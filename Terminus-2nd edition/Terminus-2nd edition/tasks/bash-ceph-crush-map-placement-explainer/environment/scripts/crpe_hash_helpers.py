"""Reference hash helpers mirrored by pytest contract math."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def json_digest(body: dict[str, Any]) -> str:
    return sha256_hex(json.dumps(body, sort_keys=True).encode())
