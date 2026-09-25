"""Hidden fixture placement trace tests."""

from __future__ import annotations

import json
from pathlib import Path

from crpe_cli_support import run_pipeline, wipe
from crpe_contract_math import reference_ledger

HIDDEN_ROOT = Path("/opt/verifier-fixtures/crpe/maps")


def test_tb3_rand_weight_hidden_matches_reference():
    """Verify TB3 randomized weight map ledger matches independent reference math."""
    wipe()
    out = run_pipeline(
        "tb3-rand-weight-pool",
        "run-tb3-rand",
        0,
        9,
        map_root=HIDDEN_ROOT,
    )
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_ledger(HIDDEN_ROOT / "tb3-rand-weight-pool", "run-tb3-rand", 0, 9)
    assert rep["pg_traces"] == ref["pg_traces"]
    assert rep["ledger_digest"] == ref["ledger_digest"]


def test_tb3_out_osd_hidden_excludes_ineligible():
    """Verify TB3 out-osd trap hidden map never selects down or out osds."""
    wipe()
    out = run_pipeline(
        "tb3-out-osd-trap",
        "run-tb3-out",
        0,
        7,
        map_root=HIDDEN_ROOT,
    )
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_ledger(HIDDEN_ROOT / "tb3-out-osd-trap", "run-tb3-out", 0, 7)
    assert rep["pg_traces"] == ref["pg_traces"]
    for row in rep["pg_traces"]:
        assert 11 not in row["acting_set"]
        assert 12 not in row["acting_set"]
