"""Staging artifact policy for digest composition and emit behavior."""

from __future__ import annotations

import hashlib
import json
from typing import Any

USE_INVENTORY_IGNORE = False
DIGEST_FINDINGS = False
EXPORT_REOPEN = True


def compute_staging_digest(host_rows: list[dict[str, Any]], findings: list[dict[str, Any]]) -> str:
    """Return the current staging digest policy used by the scan stage."""
    hosts_blob = "\n".join(json.dumps(row, sort_keys=True) for row in host_rows).encode()
    if DIGEST_FINDINGS:
        findings_blob = "\n".join(json.dumps(row, sort_keys=True) for row in findings).encode()
        return hashlib.sha256(hosts_blob + findings_blob).hexdigest()
    return hashlib.sha256(hosts_blob).hexdigest()
