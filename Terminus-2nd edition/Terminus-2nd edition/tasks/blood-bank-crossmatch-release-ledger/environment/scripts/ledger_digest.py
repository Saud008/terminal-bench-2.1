"""Ledger digest helper aligned with release-ledger-contract sha256 rules."""

from __future__ import annotations

import hashlib
import json


def ledger_digest(releases: list[dict]) -> str:
    payload = json.dumps(releases, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
