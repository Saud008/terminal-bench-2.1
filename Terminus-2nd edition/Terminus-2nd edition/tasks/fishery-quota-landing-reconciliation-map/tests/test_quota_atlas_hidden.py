"""Hidden fqrctl traps under FQR_FIXTURE_ROOT."""

from __future__ import annotations

import json
import os
from pathlib import Path

from quota_atlas_verifier import (
    audit_rows_close,
    emit_atlas,
    reference_atlas_from_season,
    species_rows_close,
)


def test_hidden_alias_mix_atlas():
    """Hidden alias mix atlas rows match contract math under /opt/verifier-fixtures/fqr."""
    os.environ["FQR_FIXTURE_ROOT"] = "/opt/verifier-fixtures/fqr"
    hidden = Path("/opt/verifier-fixtures/fqr/alias-mix-trap")
    out = emit_atlas("alias-mix-trap", "tok-hid")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas_from_season(hidden, "tok-hid")
    species_rows_close(rep["species_rows"], ref["species_rows"])


def test_hidden_spa_closure_audit():
    """Hidden SPA closure rejects in-area landing audit rows."""
    os.environ["FQR_FIXTURE_ROOT"] = "/opt/verifier-fixtures/fqr"
    hidden = Path("/opt/verifier-fixtures/fqr/alias-mix-trap")
    out = emit_atlas("alias-mix-trap", "tok-hc")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas_from_season(hidden, "tok-hc")
    audit_rows_close(rep["landing_audit"], ref["landing_audit"])
