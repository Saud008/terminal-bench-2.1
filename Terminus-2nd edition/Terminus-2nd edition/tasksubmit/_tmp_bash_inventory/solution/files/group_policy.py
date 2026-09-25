"""Canonical runtime policy for lineage expansion and precedence order."""

from __future__ import annotations

CHILDREN_FIRST = True
HOST_BEFORE_GROUPS = False


def host_group_flags() -> tuple[bool, bool]:
    """Return the scan-time lineage and precedence switches."""
    return CHILDREN_FIRST, HOST_BEFORE_GROUPS


def lineage_policy_summary() -> dict[str, bool]:
    """Expose the policy in a structured form for smoke checks."""
    return {
        "children_first": CHILDREN_FIRST,
        "host_before_groups": HOST_BEFORE_GROUPS,
    }
