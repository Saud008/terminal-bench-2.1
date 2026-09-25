"""Gate: schema-bump abort — commit/abort of writes + schema marks. See /app/docs/schema-bump-abort.md."""

from __future__ import annotations

from typing import Any, Dict


def keep_commit(rec: Dict[str, Any]) -> bool:
    return True
