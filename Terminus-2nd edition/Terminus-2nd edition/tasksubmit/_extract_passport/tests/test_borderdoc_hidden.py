"""Hidden traps — TB3 fixture dir."""

from __future__ import annotations

import json
import os
from pathlib import Path

from validity_refmath import reference_decisions
from validity_runner import DECISION_JSON, HIDDEN_ROOT, run_pipeline, wipe_state


def test_borderdoc_hidden_expiry_trap_needs_inclusive_window() -> None:
    """Hidden expiry scenario requires inclusive passport expiry fix."""
    wipe_state()
    root = Path("/opt/verifier-fixtures/borderdocctl")
    if os.environ.get("TB3_FIXTURE_DIR"):
        root = Path(os.environ["TB3_FIXTURE_DIR"])
    run_pipeline("hidden-expiry-trap", fixture_root_path=root)
    ref = reference_decisions("hidden-expiry-trap", root)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"] == ref["decisions"]
    assert body["decisions"][0]["allowed_entry"] is True


def test_borderdoc_hidden_precedence_trap_needs_federal_cap() -> None:
    """Hidden precedence scenario requires federal over port max_stay."""
    wipe_state()
    root = HIDDEN_ROOT
    run_pipeline("hidden-precedence-trap", fixture_root_path=root)
    ref = reference_decisions("hidden-precedence-trap", root)
    body = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert body["decisions"] == ref["decisions"]
    assert body["decisions"][0]["max_stay_allowed"] == 60
