"""Hidden /opt/verifier-fixtures traps for SBOM/VEX atlas."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from reachvex_cli_lane import EXPOSURE_LEDGER, TB3_DEV_TRAP, TB3_EXPIRED, reach_lane_full_pass, reach_lane_read_bundle, reach_lane_reset
from reachvex_ref_math import reference_export, reference_stage_from_bundle


def test_reachvex_tb3_fixture_paths_on_disk():
    """Hidden bundles live under /opt/verifier-fixtures/vex-bundles/."""
    assert TB3_EXPIRED == Path("/opt/verifier-fixtures/vex-bundles/tb3-expired-waiver/bundle.json")
    assert TB3_DEV_TRAP == Path("/opt/verifier-fixtures/vex-bundles/tb3-dev-edge-trap/bundle.json")
    assert TB3_EXPIRED.is_file()
    assert TB3_DEV_TRAP.is_file()


def test_reachvex_tb3_expired_waiver_falls_back_affected():
    """expiry-windows.md expired not_affected ignored."""
    reach_lane_reset()
    reach_lane_full_pass(TB3_EXPIRED)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    ref = reference_export(
        reference_stage_from_bundle(reach_lane_read_bundle(TB3_EXPIRED)),
        now=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    row = next(i for i in got["impacts"] if i["vuln_id"] == "CVE-2024-9001")
    ref_row = next(i for i in ref["impacts"] if i["vuln_id"] == "CVE-2024-9001")
    assert row["effective_status"] == ref_row["effective_status"] == "affected"
    assert row["waiver"] is None


def test_reachvex_tb3_dev_edge_trap_no_codecrown():
    """tb3-dev-edge-trap bundle must not emit codecrown impacts."""
    reach_lane_reset()
    reach_lane_full_pass(TB3_DEV_TRAP)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    codecrown = [i for i in got["impacts"] if "codecrown" in i["package_purl"]]
    assert codecrown == []
