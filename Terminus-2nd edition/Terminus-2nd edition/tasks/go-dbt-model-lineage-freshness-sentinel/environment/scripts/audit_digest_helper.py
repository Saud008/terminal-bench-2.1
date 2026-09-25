"""Digest helper mirroring alert-export-contract audit_digest rules."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def audit_digest(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()
