"""Reference atlas hashing helpers used when building OCI fixture archives."""

from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path


def sha256_lines(lines: list[str]) -> str:
    payload = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def list_tar_paths(tar_path: Path) -> list[str]:
    with tarfile.open(tar_path, "r:*") as archive:
        return [member.name for member in archive.getmembers()]
