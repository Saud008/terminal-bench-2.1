#!/usr/bin/env python3
"""Wire buffer SHA-256 helper for verifier scripts (not on fbdecode hot path)."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
