"""Hidden shift-pl traps with randomized region aliases."""

from __future__ import annotations

import json
import os
from pathlib import Path

from shift_pl_cli_support import pipeline, wipe
from shift_pl_oracle import reference_atlas

HIDDEN_SCENARIO = Path("/opt/verifier-fixtures/shift-pl/carbon-alias-mix")


def test_hidden_plan_digest_from_verifier_fixtures():
    """Verifier-fixtures scenario must yield stable plan_digest across repeated exports."""
    os.environ["SHIFT_SCENARIO_ROOT"] = "/opt/verifier-fixtures/shift-pl"
    wipe()
    out1 = pipeline("carbon-alias-mix", "run-hdig-a")
    wipe()
    out2 = pipeline("carbon-alias-mix", "run-hdig-a")
    assert json.loads(out1.read_text())["plan_digest"] == json.loads(out2.read_text())["plan_digest"]


def test_hidden_alias_mix_reference():
    """Hidden trap: /opt/verifier-fixtures/shift-pl carbon-alias-mix randomized aliases."""
    os.environ["SHIFT_SCENARIO_ROOT"] = "/opt/verifier-fixtures/shift-pl"
    wipe()
    out = pipeline("carbon-alias-mix", "run-hidden")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(HIDDEN_SCENARIO, "run-hidden")
    assert rep["assignments"] == ref["assignments"]
    assert rep["blocked_jobs"] == ref["blocked_jobs"]


def test_hidden_quota_ledger_carry():
    """TB3 hidden fixture quota carry must match independent oracle ledger rows."""
    os.environ["SHIFT_SCENARIO_ROOT"] = "/opt/verifier-fixtures/shift-pl"
    wipe()
    out = pipeline("carbon-alias-mix", "run-hq")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(HIDDEN_SCENARIO, "run-hq")
    assert rep["quota_ledger"] == ref["quota_ledger"]
