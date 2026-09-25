"""Impact rollup lane tests for SBOM/VEX atlas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reachvex_cli_lane import (
    CHAIN_BUNDLE,
    EXPOSURE_LEDGER,
    MINIMAL_BUNDLE,
    VEXATLAS_BIN,
    reach_lane_rollup_ledger,
    reach_lane_full_pass,
    reach_lane_capture_bundle,
    reach_lane_read_bundle,
    reach_lane_reset,
    reach_lane_spawn_cli,
)
from reachvex_ref_math import reference_export, reference_stage_from_bundle


@pytest.fixture(autouse=True)
def reach_lane_clean():
    reach_lane_reset()
    yield
    reach_lane_reset()


def test_reachvex_impact_atlas_output_path():
    """Instruction requires /app/output/exposure-ledger.json rollup artifact."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    assert EXPOSURE_LEDGER == Path("/app/output/exposure-ledger.json")
    assert EXPOSURE_LEDGER.is_file()


def test_reachvex_vexatlas_binary_present():
    """Instruction requires /app/bin/vexatlas built from workspace."""
    assert Path(VEXATLAS_BIN).is_file()


def test_reachvex_minimal_fixture_bundle_id():
    """Instruction cites bundled minimal bundle manifest."""
    assert MINIMAL_BUNDLE.is_file()
    data = reach_lane_read_bundle(MINIMAL_BUNDLE)
    assert data["bundle_id"] == "minimal"


def test_reachvex_export_without_capture_exit_three():
    """rollup without capture exits code 3 per sbom-vex-workflow.md."""
    result = reach_lane_spawn_cli([VEXATLAS_BIN, "rollup", "--output", str(EXPOSURE_LEDGER)], check=False)
    assert result.returncode == 3


def test_reachvex_export_writes_impact_atlas():
    """rollup writes exposure-ledger.json per exposure-ledger-schema.md."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    assert EXPOSURE_LEDGER.is_file()
    doc = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    assert doc["bundle_id"] == "minimal"
    assert len(doc["impacts"]) >= 1


def test_reachvex_tlskit_not_affected_waiver_row():
    """VEX precedence picks not_affected for tlskit waiver row."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    ref = reference_export(reference_stage_from_bundle(reach_lane_read_bundle(MINIMAL_BUNDLE)))
    got_row = next(i for i in got["impacts"] if i["vuln_id"] == "CVE-2024-1001" and "tlskit" in i["package_purl"])
    ref_row = next(i for i in ref["impacts"] if i["vuln_id"] == "CVE-2024-1001" and "tlskit" in i["package_purl"])
    assert got_row["effective_status"] == ref_row["effective_status"] == "not_affected"
    assert got_row["waiver"]["statement_id"] == ref_row["waiver"]["statement_id"]


def test_reachvex_logfmt_affected_no_waiver():
    """Affected packages omit waiver evidence."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    row = next(i for i in got["impacts"] if "logfmt" in i["package_purl"] and i["vuln_id"] == "CVE-2024-2002")
    assert row["effective_status"] == "affected"
    assert row["waiver"] is None


def test_reachvex_export_digest_reference_parity():
    """export_digest uses compact sorted impact bytes."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    ref = reference_export(reference_stage_from_bundle(reach_lane_read_bundle(MINIMAL_BUNDLE)))
    assert got["export_digest"] == ref["export_digest"]


def test_reachvex_impacts_sorted_binary_package_vuln():
    """exposure-ledger-schema.md sort order binary, package_purl, vuln_id."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    keys = [(i["binary"], i["package_purl"], i["vuln_id"]) for i in got["impacts"]]
    assert keys == sorted(keys)


def test_reachvex_export_trailing_newline():
    """impact rollup file ends with single trailing newline."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    raw = EXPOSURE_LEDGER.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert not raw.endswith("\n\n")


def test_reachvex_chain_tokenhash_transitive_reach():
    """reachability-graph.md transitive runtime reachability for chain bundle."""
    reach_lane_full_pass(CHAIN_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    rows = [i for i in got["impacts"] if "tokenhash" in i["package_purl"] and i["vuln_id"] == "CVE-2024-3003"]
    assert len(rows) == 1


def test_reachvex_chain_vex_not_affected_beats_fixed():
    """vex-precedence.md not_affected wins over fixed for tokenhash."""
    reach_lane_full_pass(CHAIN_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    row = next(i for i in got["impacts"] if "tokenhash" in i["package_purl"] and i["vuln_id"] == "CVE-2024-3003")
    assert row["effective_status"] == "not_affected"
    assert row["waiver"] is not None


def test_reachvex_chain_dev_edge_skips_metrics():
    """dev edge_kind ignored for runtime reachability."""
    reach_lane_full_pass(CHAIN_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    metrics_rows = [i for i in got["impacts"] if "metrics-lite" in i["package_purl"]]
    assert metrics_rows == []


def test_reachvex_chain_authcore_under_investigation():
    """authcore row uses under_investigation when no higher precedence applies."""
    reach_lane_full_pass(CHAIN_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    row = next(i for i in got["impacts"] if "authcore" in i["package_purl"])
    assert row["effective_status"] == "under_investigation"


def test_reachvex_export_reads_staging_not_bundle():
    """rollup must not reopen bundle.json after capture."""
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    bundle_mtime = MINIMAL_BUNDLE.stat().st_mtime
    reach_lane_rollup_ledger()
    assert MINIMAL_BUNDLE.stat().st_mtime == bundle_mtime
    assert EXPOSURE_LEDGER.is_file()


def test_reachvex_minimal_full_reference_parity():
    """All minimal impacts match independent reference rollup."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    ref = reference_export(reference_stage_from_bundle(reach_lane_read_bundle(MINIMAL_BUNDLE)))
    assert got["impacts"] == ref["impacts"]
