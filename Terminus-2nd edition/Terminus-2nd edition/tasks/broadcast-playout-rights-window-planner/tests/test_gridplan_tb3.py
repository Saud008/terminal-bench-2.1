"""TB3 hidden fixture overlay traps."""
from __future__ import annotations

import json
import os

from bcast_synd_refmath import reference_plan
from bcast_synd_cli import HIDDEN_ROOT, PLAN_JSON, run_pipeline, wipe_state

HIDDEN_RIGHTS = "hidden-rights-trap"
HIDDEN_BLACKOUT = "hidden-blackout-trap"


def test_gridwin_hidden_rights_trap():
    """/opt/verifier-fixtures/gridplan hidden rights overlap trap."""
    wipe_state()
    run_pipeline(HIDDEN_RIGHTS, fixture_root=HIDDEN_ROOT, extra_env={"TB3_FIXTURE_DIR": str(HIDDEN_ROOT)})
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    ref = reference_plan(HIDDEN_ROOT, HIDDEN_RIGHTS)
    assert plan["entries"] == ref["entries"]


def test_gridwin_hidden_blackout_trap():
    """TB3_FIXTURE_DIR /opt/verifier-fixtures/gridplan blackout boundary trap."""
    wipe_state()
    run_pipeline(HIDDEN_BLACKOUT, fixture_root=HIDDEN_ROOT, extra_env={"TB3_FIXTURE_DIR": str(HIDDEN_ROOT)})
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    ref = reference_plan(HIDDEN_ROOT, HIDDEN_BLACKOUT)
    assert plan["entries"] == ref["entries"]


def test_gridwin_hidden_rights_bias_env():
    """TB3_RIGHTS_BIAS env adjusts overlap epsilon on hidden rights trap fixtures."""
    wipe_state()
    run_pipeline(HIDDEN_RIGHTS, fixture_root=HIDDEN_ROOT, extra_env={"TB3_RIGHTS_BIAS": "0.001"})
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    ref = reference_plan(HIDDEN_ROOT, HIDDEN_RIGHTS)
    assert len(plan["entries"]) == len(ref["entries"])
    os.environ.pop("TB3_RIGHTS_BIAS", None)
