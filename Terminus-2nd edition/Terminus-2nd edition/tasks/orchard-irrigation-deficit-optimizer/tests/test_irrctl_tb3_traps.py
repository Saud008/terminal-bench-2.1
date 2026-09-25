"""Hidden irrctl traps with randomized field aliases."""

from __future__ import annotations

import json
import os
from pathlib import Path

from irrctl_subprocess_helpers import pipeline, wipe
from irrctl_plan_math import independent_plan, assert_assignments_close, assert_quota_close


def test_hidden_alias_mix_assignments():
    """Hidden orchard alias mix verifies assignments against independent math under ORCHARD_SCENARIO_ROOT."""
    hidden_root = Path("/opt/verifier-fixtures/irrctl/orchard-alias-mix")
    os.environ["ORCHARD_SCENARIO_ROOT"] = "/opt/verifier-fixtures/irrctl"
    wipe()
    out = pipeline("orchard-alias-mix", "run-hidden")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = independent_plan(hidden_root, "run-hidden")
    assert_assignments_close(rep["assignments"], ref["assignments"])


def test_hidden_quota_ledger():
    """Hidden quota ledger trap verifies carryover rows against independent math."""
    hidden_root = Path("/opt/verifier-fixtures/irrctl/orchard-alias-mix")
    os.environ["ORCHARD_SCENARIO_ROOT"] = "/opt/verifier-fixtures/irrctl"
    wipe()
    out = pipeline("orchard-alias-mix", "run-hq")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = independent_plan(hidden_root, "run-hq")
    assert_quota_close(rep["quota_ledger"], ref["quota_ledger"])
