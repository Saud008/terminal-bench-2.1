"""Hidden verifier traps for calloutd."""

from __future__ import annotations

import json
import os
from pathlib import Path

from ref_dispatch_math import reference_roster, reference_scores
from callout_pipeline import ROSTER_JSON, run_pipeline, wipe_state

HIDDEN_ROOT = Path("/opt/verifier-fixtures/calloutd")


def test_emcd_hidden_access_end_trap() -> None:
    """TB3 hidden bundle requires inclusive access end_minute."""
    wipe_state()
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    try:
        run_pipeline("hidden-access-end-trap", fixture_root=HIDDEN_ROOT)
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_roster(HIDDEN_ROOT, "hidden-access-end-trap")
        assert body["assignments"] == ref["assignments"]
    finally:
        os.environ.pop("TB3_FIXTURE_DIR", None)


def test_emcd_hidden_sla_tier_trap() -> None:
    """TB3 hidden bundle requires gold SLA tier_rank precedence."""
    wipe_state()
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    try:
        run_pipeline("hidden-sla-tier-trap", fixture_root=HIDDEN_ROOT)
        ref_scores = reference_scores(HIDDEN_ROOT, "hidden-sla-tier-trap")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_roster(HIDDEN_ROOT, "hidden-sla-tier-trap")
        assert body["breach_horizon_summary"] == ref["breach_horizon_summary"]
        assert ref_scores[0]["sla_urgency"] > 0
    finally:
        os.environ.pop("TB3_FIXTURE_DIR", None)
