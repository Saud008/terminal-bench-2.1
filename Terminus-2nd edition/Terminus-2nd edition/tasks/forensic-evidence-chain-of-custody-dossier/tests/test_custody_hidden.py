"""Hidden fixture tests using TB3_CASE_ROOT."""
from __future__ import annotations

import json
from pathlib import Path

from custody_cli_helpers import run_pipeline, wipe
from custody_verifier_math import reference_dossier

HIDDEN = Path("/opt/verifier-fixtures/forensic/cases")
CAT = Path("/app/catalog/storage-locations.json")


def test_hidden_seal_overlay_detects_mid_chain_break() -> None:
    """Verify hidden TB3 bundle seal break on second transfer is detected."""
    wipe()
    case_id = "CASE-HIDDEN-901"
    env = {"TB3_CASE_ROOT": str(HIDDEN)}
    out = run_pipeline(case_id, "hidden-seal-overlay", env=env)
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_dossier(case_id, HIDDEN / "hidden-seal-overlay.json", CAT)
    assert got["summary"]["seal_breaks"] == ref["summary"]["seal_breaks"] == 1
    assert got["integrity_findings"] == ref["integrity_findings"]


def test_hidden_overlay_still_preserves_lineage_edge_count() -> None:
    """Verify hidden bundle retains two lineage edges before finding tally."""
    wipe()
    case_id = "CASE-HIDDEN-901"
    env = {"TB3_CASE_ROOT": str(HIDDEN)}
    out = run_pipeline(case_id, "hidden-seal-overlay", env=env)
    got = json.loads(out.read_text(encoding="utf-8"))
    assert len(got["lineage_edges"]) == 2
