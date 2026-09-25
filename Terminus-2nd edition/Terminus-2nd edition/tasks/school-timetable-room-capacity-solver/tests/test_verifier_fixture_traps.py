"""TB3 hidden fixture overlay traps."""
from __future__ import annotations

import json
import os

from ttalloc_refmath import reference_assignments
from ttalloc_driver import ATLAS_JSON, HIDDEN_ROOT, run_pipeline, wipe_state

HIDDEN_LAB = "hidden-lab-trap"
HIDDEN_SPLIT = "hidden-split-trap"


def test_ttalloc_cap_hidden_lab_trap():
    """Verifier contract: hidden lab trap."""
    wipe_state()
    # Uses /opt/verifier-fixtures/ttalloc via TB3_FIXTURE_DIR override path.
    run_pipeline(HIDDEN_LAB, fixture_root=HIDDEN_ROOT, extra_env={"TB3_FIXTURE_DIR": str(HIDDEN_ROOT)})
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(HIDDEN_ROOT, HIDDEN_LAB)
    assert atlas["assignments"] == ref["assignments"]


def test_ttalloc_cap_hidden_split_trap():
    """Verifier contract: hidden split trap."""
    wipe_state()
    # Hidden overlay under /opt/verifier-fixtures/ttalloc scenarios.
    run_pipeline(HIDDEN_SPLIT, fixture_root=HIDDEN_ROOT, extra_env={"TB3_FIXTURE_DIR": str(HIDDEN_ROOT)})
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(HIDDEN_ROOT, HIDDEN_SPLIT)
    assert atlas["assignments"] == ref["assignments"]


def test_ttalloc_cap_hidden_score_bias_env():
    """Verifier contract: hidden score bias env."""
    wipe_state()
    run_pipeline(HIDDEN_LAB, fixture_root=HIDDEN_ROOT, extra_env={"TB3_SCORE_BIAS": "0.001"})
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(HIDDEN_ROOT, HIDDEN_LAB)
    assert len(atlas["assignments"]) == len(ref["assignments"])
    os.environ.pop("TB3_SCORE_BIAS", None)
