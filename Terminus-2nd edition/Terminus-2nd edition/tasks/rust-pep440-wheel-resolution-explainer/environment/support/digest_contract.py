"""Shared digest helpers referenced by verifier contract math."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_sha256(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
