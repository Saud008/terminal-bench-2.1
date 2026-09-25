"""Verifier overlay traps for plan waiver and step therapy boundaries."""

from __future__ import annotations

from formulatrix_refmath import reference_matrix
from formulatrix_runner import (
    FX_MATRIX,
    FX_OVERLAY,
    fx_clean_state,
    fx_read_json,
    fx_run_overlay_scenario,
)


class FormularyVerifierOverlay:
    def test_fxv01_overlay_plan_waiver_trap(self) -> None:
        """Hidden override-precedence scenario matches reference requires_pa."""
        fx_clean_state()
        overlay_env = {"TB3_FIXTURE_DIR": str(FX_OVERLAY)}
        fx_run_overlay_scenario("override-precedence-trap", FX_OVERLAY, extra_env=overlay_env)
        body = fx_read_json(FX_MATRIX)
        ref = reference_matrix("override-precedence-trap", FX_OVERLAY)
        assert body["rows"][0]["requires_pa"] == ref["rows"][0]["requires_pa"]

    def test_fxv02_overlay_step_prereq_trap(self) -> None:
        """Hidden step-chain boundary keeps incomplete rows aligned with reference."""
        fx_clean_state()
        overlay_env = {"TB3_FIXTURE_DIR": str(FX_OVERLAY)}
        fx_run_overlay_scenario("step-chain-boundary-trap", FX_OVERLAY, extra_env=overlay_env)
        body = fx_read_json(FX_MATRIX)
        ref = reference_matrix("step-chain-boundary-trap", FX_OVERLAY)
        body_flags = sorted(
            (r["ndc_normalized"], r["step_complete"]) for r in body["rows"]
        )
        ref_flags = sorted(
            (r["ndc_normalized"], r["step_complete"]) for r in ref["rows"]
        )
        assert body_flags == ref_flags
        assert any(not flag for _, flag in ref_flags)
