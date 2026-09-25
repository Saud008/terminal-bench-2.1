"""Canonical staging artifact policy for digest composition and emit behavior."""

from __future__ import annotations

import hashlib
import json
from typing import Any

USE_INVENTORY_IGNORE = True
DIGEST_FINDINGS = True
EXPORT_REOPEN = False


def _ndjson_bytes(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        return b""
    return (
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"
    ).encode()


def compute_staging_digest(host_rows: list[dict[str, Any]], findings: list[dict[str, Any]]) -> str:
    """Hash staged NDJSON bytes; findings inclusion follows DIGEST_FINDINGS."""
    hosts_blob = _ndjson_bytes(host_rows)
    if DIGEST_FINDINGS:
        return hashlib.sha256(hosts_blob + _ndjson_bytes(findings)).hexdigest()
    return hashlib.sha256(hosts_blob).hexdigest()


def emit_reopens_inventory() -> bool:
    """The emit stage must reuse staged artifacts and never rescan the tree."""
    return EXPORT_REOPEN
