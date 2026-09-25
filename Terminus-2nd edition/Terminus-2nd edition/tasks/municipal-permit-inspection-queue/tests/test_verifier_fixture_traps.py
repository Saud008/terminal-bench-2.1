"""Hidden verifier traps for mpiqctl."""

from __future__ import annotations

import json
import os
from pathlib import Path

from permit_ref_math import reference_entries, reference_queue
from permit_queue_driver import MANIFEST_JSON, run_pipeline, wipe_state

HIDDEN_ROOT = Path("/opt/verifier-fixtures/mpiqctl")


def test_mpq_hidden_blackout_end_trap() -> None:
    """TB3 hidden bundle requires inclusive blackout end_day."""
    wipe_state()
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    try:
        run_pipeline("hidden-clean-queue", fixture_root=HIDDEN_ROOT)
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_queue(HIDDEN_ROOT, "hidden-clean-queue")
        assert body["queue_entries"] == ref["queue_entries"]
    finally:
        os.environ.pop("TB3_FIXTURE_DIR", None)


def test_mpq_hidden_hold_bias_trap() -> None:
    """TB3 hidden bundle applies TB3_HOLD_BIAS to zoning hold precedence."""
    wipe_state()
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    os.environ["TB3_HOLD_BIAS"] = "1"
    try:
        run_pipeline("hidden-violation-priority", fixture_root=HIDDEN_ROOT)
        ref = reference_entries(HIDDEN_ROOT, "hidden-violation-priority")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        assert body["queue_entries"] == ref
    finally:
        os.environ.pop("TB3_FIXTURE_DIR", None)
        os.environ.pop("TB3_HOLD_BIAS", None)
