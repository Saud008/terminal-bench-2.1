"""Runtime policy for group lineage and variable precedence order."""

from __future__ import annotations

CHILDREN_FIRST = False
HOST_BEFORE_GROUPS = True


def host_group_flags() -> tuple[bool, bool]:
    """Return the lineage and precedence switches used by inventory_engine."""
    return CHILDREN_FIRST, HOST_BEFORE_GROUPS
