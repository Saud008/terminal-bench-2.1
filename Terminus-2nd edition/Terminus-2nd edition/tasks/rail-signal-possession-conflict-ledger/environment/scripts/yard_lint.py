"""Yard fixture lint — homes verifier helper imports for collapse GX8."""

from __future__ import annotations

import interval_checker
import railpos_cli_paths


def lint_fixture_count() -> int:
    return len(railpos_cli_paths.SEED_POOL)


def lint_reference_available() -> bool:
    return callable(getattr(interval_checker, "reference_ledger", None))
