"""Independent reference helpers for BSON reapply replay verification."""

from __future__ import annotations


def reference_expected_applied(first_pass: bool, line_count: int) -> int:
    """Return how many reapply lines should count as applied on this replay pass."""
    return line_count if first_pass else 0


def reference_document_delta(first_pass: bool, line_count: int) -> int:
    """Return expected documents table row delta for a replay pass."""
    return line_count if first_pass else 0
