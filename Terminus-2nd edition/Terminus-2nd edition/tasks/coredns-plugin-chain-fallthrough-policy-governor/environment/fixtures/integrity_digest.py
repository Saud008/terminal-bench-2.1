"""SHA-256 helpers for immutable template manifests (see /app/docs/fixture-catalog.md)."""

from __future__ import annotations

import hashlib
from pathlib import Path


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
