"""Subprocess CLI verifier with independent reference_* parity for vexatlas."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from reachvex_cli_lane import (
    CHAIN_BUNDLE,
    EXPOSURE_LEDGER,
    MINIMAL_BUNDLE,
    VEXATLAS_BIN,
    reach_lane_capture_bundle,
    reach_lane_full_pass,
    reach_lane_read_bundle,
    reach_lane_reset,
    reach_lane_spawn_cli,
)
from reachvex_ref_math import reference_export, reference_stage_from_bundle


def test_td3d9fa_sbom_instruction_contract_paths():
    """Instruction contract paths for chain bundle, missing bundle, run-seq, and waiver-snapshot."""
    assert Path("/app/data/bundles/chain/bundle.json").is_file()
    assert Path("/app/state/run-seq.json").parent.is_dir()
    assert Path("/app/state/waiver-snapshot.json").parent.is_dir()
    reach_lane_reset()
    missing = reach_lane_spawn_cli(
        [VEXATLAS_BIN, "capture", "--bundle", "/app/data/bundles/missing/bundle.json"],
        check=False,
    )
    assert missing.returncode == 2
    reach_lane_capture_bundle(CHAIN_BUNDLE)
    assert Path("/app/state/run-seq.json").is_file()
    assert Path("/app/state/waiver-snapshot.json").is_file()


def test_td3d9fa_sbom_subprocess_cli_capture_lane():
    """Every verifier run executes vexatlas via subprocess."""
    reach_lane_reset()
    result = reach_lane_spawn_cli([VEXATLAS_BIN, "capture", "--bundle", str(MINIMAL_BUNDLE)], check=False)
    assert result.returncode == 0


def test_td3d9fa_sbom_reference_stage_cli_parity():
    """Staging snapshot matches reference_stage_from_bundle independent math."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    from reachvex_cli_lane import WAIVER_SNAPSHOT

    assert json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))["staging_digest"] == reference_stage_from_bundle(
        reach_lane_read_bundle(MINIMAL_BUNDLE)
    )["staging_digest"]
    stage = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))
    ref = reference_stage_from_bundle(reach_lane_read_bundle(MINIMAL_BUNDLE))
    assert stage["bundle_id"] == ref["bundle_id"]
    assert stage["packages"] == ref["packages"]


def test_td3d9fa_sbom_reference_export_cli_parity():
    """Impact atlas matches reference_export after full pipeline."""
    reach_lane_full_pass(MINIMAL_BUNDLE)
    assert json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))["impacts"] == reference_export(
        reference_stage_from_bundle(reach_lane_read_bundle(MINIMAL_BUNDLE))
    )["impacts"]
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    ref = reference_export(reference_stage_from_bundle(reach_lane_read_bundle(MINIMAL_BUNDLE)))
    assert got["export_digest"] == ref["export_digest"]


def test_td3d9fa_sbom_subprocess_export_exit_three_without_capture():
    """rollup without capture exits 3 per sbom-vex-workflow.md."""
    reach_lane_reset()
    result = subprocess.run(
        [VEXATLAS_BIN, "rollup", "--output", str(EXPOSURE_LEDGER)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 3


def test_td3d9fa_sbom_chain_bundle_reference_export_parity():
    """Chain bundle rollup matches independent reference across transitive edges."""
    reach_lane_full_pass(CHAIN_BUNDLE)
    got = json.loads(EXPOSURE_LEDGER.read_text(encoding="utf-8"))
    ref = reference_export(reference_stage_from_bundle(reach_lane_read_bundle(CHAIN_BUNDLE)))
    assert got["impacts"] == ref["impacts"]
