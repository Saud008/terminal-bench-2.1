"""hashlib seal digest helper for conform stage."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def seal_sha256(edits: list[dict[str, Any]], diagnostics: list[dict[str, Any]], include_diag: bool) -> str:
    body: dict[str, Any] = {"edits": edits}
    if include_diag:
        body["diagnostics"] = diagnostics
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
