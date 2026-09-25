"""Vault marker policy shared by scan and emit stages."""

from __future__ import annotations

VAULT_PREFIX = "$ANSIBLE_VAULT;"


def has_vault_prefix(value: str, prefix: str = VAULT_PREFIX) -> bool:
    """Return True when the raw value begins with the vault prefix."""
    return value.startswith(prefix)
