"""Plan digest helper — mirrors shift-schedule-atlas-schema.md plan_digest rules."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def plan_digest(assignments: list[dict[str, Any]], blocked_jobs: list[dict[str, Any]]) -> str:
    body = {"assignments": assignments, "blocked_jobs": blocked_jobs}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
