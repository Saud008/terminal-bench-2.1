"""TB3 / opt verifier hidden-trap and depth coverage for slsacip."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import slsacip_harness as harness

WAVE_NORTH = "/app/fixtures/pull-waves/wave-north.jsonl"
WAVE_EAST = "/app/fixtures/pull-waves/wave-east.jsonl"


def test_tb3_verifier_math_stays_under_tests_not_opt():
    """Reference math lives under /tests only — not agent-readable /opt."""
    math_path = harness.MATH_MODULE_PATH.resolve()
    assert math_path.is_file()
    assert math_path.name == "slsacip_batch_math.py"
    assert "tests" in math_path.parts
    assert not Path("/opt/verifier-slsacip-math/slsacip_batch_math.py").exists()


def test_tb3_alternate_env_does_not_change_bundled_wave_north():
    """TB3_SLSACIP_SEED must not silently rewrite bundled wave-north without config."""
    os.environ["TB3_SLSACIP_SEED"] = "tb3-noise-seed"
    try:
        harness.reset_state()
        report = harness.run_attest(WAVE_NORTH)
        reference = harness.reference_report(WAVE_NORTH)
        assert report == reference
    finally:
        os.environ.pop("TB3_SLSACIP_SEED", None)


def test_tb3_incomplete_baseline_diverges(fresh_workspace):
    """Swapping verifier-incomplete-slsa baseline must fail reference seal."""
    harness.swap_layers([])
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH)
    reference = harness.reference_report(WAVE_NORTH)
    assert report != reference


def test_quorum_k_fingerprint_present_on_ledger():
    """Sealed ledger must expose quorum_k and audit_digest fields."""
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH)
    assert report["quorum_k"] == 2
    assert len(report["audit_digest"]) == 64


def test_east_wave_preserves_request_order():
    """Pull-wave east results must preserve JSONL request order vs reference."""
    harness.reset_state()
    report = harness.run_attest(WAVE_EAST)
    reference = harness.reference_report(WAVE_EAST)
    assert [r["request_id"] for r in report["results"]] == [
        r["request_id"] for r in reference["results"]
    ]


def test_subprocess_slsacip_help_exits_clean():
    """CLI help via subprocess must exit without crashing the binary."""
    proc = subprocess.run(
        [harness.SLSACIP_BIN, "help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode in (0, 2)


def test_ledger_schema_is_slsacip_attest_v1():
    """Default sealed ledger schema must be slsacip.attest.v1."""
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH)
    assert report["schema"] == "slsacip.attest.v1"
    assert Path("/app/output/slsa-admission-ledger.json").is_file()


def test_trust_witness_file_mtime_after_attest():
    """Trust witness path must exist after attest completes."""
    harness.reset_state()
    harness.run_attest(WAVE_NORTH)
    assert harness.WITNESS_PATH.is_file()
