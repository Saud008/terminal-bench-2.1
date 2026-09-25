"""Staging lane contract tests for SBOM/VEX atlas capture."""

from __future__ import annotations

import json
from pathlib import Path

from reachvex_cli_lane import WAIVER_SNAPSHOT, CHAIN_BUNDLE, MINIMAL_BUNDLE, reach_lane_capture_bundle, reach_lane_reset
from reachvex_ref_math import staging_digest_from_stage


def test_reachvex_minimal_manifest_path():
    """Instruction cites /app/data/bundles/minimal/bundle.json."""
    assert MINIMAL_BUNDLE == Path("/app/data/bundles/minimal/bundle.json")
    assert MINIMAL_BUNDLE.is_file()


def test_reachvex_chain_manifest_path():
    """Instruction cites /app/data/bundles/chain/bundle.json."""
    assert CHAIN_BUNDLE == Path("/app/data/bundles/chain/bundle.json")
    assert CHAIN_BUNDLE.is_file()


def test_reachvex_atlas_stage_artifact_path():
    """Instruction requires /app/state/waiver-snapshot.json staging artifact."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    assert WAIVER_SNAPSHOT == Path("/app/state/waiver-snapshot.json")
    assert WAIVER_SNAPSHOT.is_file()


def test_reachvex_run_seq_cross_run_state():
    """Instruction tracks cross-run state at /app/state/run-seq.json."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    run_seq = Path("/app/state/run-seq.json")
    assert run_seq.is_file()


def test_reachvex_capture_writes_staging_snapshot():
    """Ingest must write /app/state/waiver-snapshot.json."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    assert WAIVER_SNAPSHOT.is_file()
    stage = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))
    assert stage["bundle_id"] == "minimal"
    assert len(stage["packages"]) == 3


def test_reachvex_chain_staging_bundle_id():
    """Chain bundle fingerprint lands in staging bundle_id."""
    reach_lane_reset()
    reach_lane_capture_bundle(CHAIN_BUNDLE)
    stage = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))
    assert stage["bundle_id"] == "chain"


def test_reachvex_purl_scheme_lowercase():
    """package-normalization.md lowercases pkg scheme for PKG:CARGO rows."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    stage = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))
    purls = {p["norm_purl"] for p in stage["packages"]}
    assert "pkg:cargo/tlskit@0.9.1" in purls


def test_reachvex_staging_packages_sorted_norm_purl():
    """Staging packages sorted by norm_purl ascending."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    stage = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))
    norms = [p["norm_purl"] for p in stage["packages"]]
    assert norms == sorted(norms)


def test_reachvex_staging_digest_reference_parity():
    """staging_digest follows package-normalization.md canonical body hash."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    stage = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))
    assert stage["staging_digest"] == staging_digest_from_stage(stage)


def test_reachvex_run_seq_created_on_capture():
    """Cross-run state tracks /app/state/run-seq.json."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    run_seq_path = Path("/app/state/run-seq.json")
    assert run_seq_path.is_file()
    data = json.loads(run_seq_path.read_text(encoding="utf-8"))
    assert "run_seq" in data


def test_reachvex_ingest_seq_stable_same_fingerprint():
    """Unchanged bundle fingerprint keeps run_seq stable."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    first = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))["ingest_seq"]
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    second = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))["ingest_seq"]
    assert second == first


def test_reachvex_ingest_seq_advances_new_fingerprint():
    """New fingerprint advances run_seq."""
    reach_lane_reset()
    reach_lane_capture_bundle(MINIMAL_BUNDLE)
    first = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))["ingest_seq"]
    reach_lane_capture_bundle(CHAIN_BUNDLE)
    second = json.loads(WAIVER_SNAPSHOT.read_text(encoding="utf-8"))["ingest_seq"]
    assert second == first + 1


def test_reachvex_missing_bundle_exit_two():
    """capture missing bundle exits code 2."""
    reach_lane_reset()
    from reachvex_cli_lane import reach_lane_spawn_cli, VEXATLAS_BIN

    result = reach_lane_spawn_cli(
        [
            VEXATLAS_BIN,
            "capture",
            "--bundle",
            "/app/data/bundles/missing/bundle.json",
        ],
        check=False,
    )
    assert result.returncode == 2
