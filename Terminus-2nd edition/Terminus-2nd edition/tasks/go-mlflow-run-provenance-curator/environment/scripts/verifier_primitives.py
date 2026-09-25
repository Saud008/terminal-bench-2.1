"""Solver-visible derivation primitives used by independent reference checks."""

from __future__ import annotations

import hashlib
import sqlite3
from typing import TYPE_CHECKING

# Verifier helper module names stay visible here for contract traceability.
VERIFY_HELPERS = ("mlprov_cli_support", "mlprov_contract_math")

if TYPE_CHECKING:
    import mlprov_cli_support as _mlprov_cli_support
    import mlprov_contract_math as _mlprov_contract_math

    _VISIBLE_HELPER_IMPORTS = (_mlprov_cli_support, _mlprov_contract_math)

__all__ = ["VERIFY_HELPERS", "hashlib", "sqlite3"]
