"""Partial seal probes: isolated layer fixes must not pass full attest reference."""

from __future__ import annotations

import pytest

import slsacip_harness as harness

WAVE_NORTH = "/app/fixtures/pull-waves/wave-north.jsonl"
ALL_LAYERS = [
    "layer_rootbind.go",
    "layer_quorumadmit.go",
    "layer_witnesswrite.go",
    "layer_sealhex.go",
]


@pytest.mark.parametrize("layer_name", ALL_LAYERS)
def test_single_layer_fix_is_insufficient(fresh_workspace, layer_name):
    """One partial layer over buggy baseline must still diverge from sealed reference."""
    harness.swap_layers([layer_name])
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH)
    reference = harness.reference_report(WAVE_NORTH)
    assert report != reference


def test_all_four_layers_together_still_insufficient(fresh_workspace):
    """Even all four probe layers leave pindeny/revokewin/predallow/buildergate buggy."""
    harness.swap_layers(ALL_LAYERS)
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH)
    reference = harness.reference_report(WAVE_NORTH)
    assert report != reference


def test_no_layers_applied_diverges_from_reference(fresh_workspace):
    """Incomplete baseline alone must fail witness/seal bind against reference."""
    harness.swap_layers([])
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH)
    reference = harness.reference_report(WAVE_NORTH)
    assert report != reference


def test_rootbind_and_quorum_layers_together_still_insufficient(fresh_workspace):
    """Rootbind+quorum partial fixes without sealhex still fail audit_digest."""
    harness.swap_layers(["layer_rootbind.go", "layer_quorumadmit.go"])
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH)
    reference = harness.reference_report(WAVE_NORTH)
    assert report != reference
