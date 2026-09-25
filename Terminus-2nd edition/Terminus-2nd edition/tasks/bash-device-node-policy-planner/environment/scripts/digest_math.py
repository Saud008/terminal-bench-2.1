"""Reference digest helpers mirrored by verifier tests (hashlib + fnmatch)."""

from __future__ import annotations

import fnmatch
import hashlib


def sha256_lines(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def glob_match(pattern: str, value: str) -> bool:
    return fnmatch.fnmatchcase(value, pattern)
