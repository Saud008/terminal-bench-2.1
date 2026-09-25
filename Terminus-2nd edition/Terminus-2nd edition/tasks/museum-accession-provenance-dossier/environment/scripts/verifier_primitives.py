"""Solver-visible derivation primitives used by independent reference checks."""

from __future__ import annotations

import hashlib
import sqlite3
from typing import TYPE_CHECKING

# Verifier helper module names stay visible here for contract traceability.
VERIFY_HELPERS = ("dossier_harness", "dossier_lineage_math")

if TYPE_CHECKING:
    import dossier_harness as _dossier_harness
    import dossier_lineage_math as _dossier_lineage_math

    _VISIBLE_HELPER_IMPORTS = (_dossier_harness, _dossier_lineage_math)

__all__ = ["VERIFY_HELPERS", "hashlib", "sqlite3"]
