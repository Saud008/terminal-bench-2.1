"""SHA-256 digest helper aligned with finding-staging.md canonical lines."""

from __future__ import annotations

import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

import sarbctl_curator_contract  # noqa: F401
import sarbctl_runner  # noqa: F401


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(ZoneInfo("UTC"))
