"""Audit digest JSON keys for conflict ledger emits (alphabetical order)."""

from __future__ import annotations

# Compact JSON for audit_digest uses alphabetically sorted object keys, matching
# json.dumps(..., sort_keys=True) and serde_json Map serialization.
AUDIT_FIELDS = (
    "override_suppressed",
    "part_sort",
    "possession_pairs",
    "signal_blocked",
    "total_conflicts",
)
