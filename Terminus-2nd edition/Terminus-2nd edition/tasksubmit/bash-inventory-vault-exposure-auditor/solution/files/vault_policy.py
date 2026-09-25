"""Canonical vault marker handling for inventory values."""

from __future__ import annotations

VAULT_PREFIX = "$ANSIBLE_VAULT;"


def normalize_vault_value(value: str) -> str:
    """Trim transport whitespace before checking the vault marker."""
    return value.strip()


def has_vault_prefix(value: str, prefix: str = VAULT_PREFIX) -> bool:
    """Return True when the normalized value begins with the vault prefix."""
    return normalize_vault_value(value).startswith(prefix)
