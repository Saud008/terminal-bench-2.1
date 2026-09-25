"""Seal digest helper — documents hashlib usage for CDR publish seal."""

from __future__ import annotations

import hashlib
import json


def seal_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()
