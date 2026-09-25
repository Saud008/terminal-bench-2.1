"""Gate: identity-bind preview — blank-node upsert binding. See /app/docs/identity-bind-preview.md."""

from __future__ import annotations

from typing import Any, Dict


def resolve_bind(g: Any, edit: Dict[str, Any]) -> str:
    return g.resolve_node(edit["node"])
