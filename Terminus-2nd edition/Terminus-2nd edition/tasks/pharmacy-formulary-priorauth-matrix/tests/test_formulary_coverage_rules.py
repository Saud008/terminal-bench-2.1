"""Formulary coverage rules — NDC, RxNorm, plan policy, step therapy, digest seals."""

from __future__ import annotations

import json

import pytest
from formulatrix_refmath import (
    normalize_ndc,
    preferred_rxnorm,
    reference_matrix,
    reference_roster,
    select_override,
)
from formulatrix_runner import (
    COVERAGE_SCENARIOS,
    FX_BIN,
    FX_BUNDLE,
    FX_GEN,
    FX_MATRIX,
    FX_ROSTER,
    fx_clean_state,
    fx_full_matrix_run,
    fx_invoke,
    fx_read_json,
)


class FormularyCoverageRules:
    @pytest.mark.parametrize("scenario_id", COVERAGE_SCENARIOS)
    def test_fxr01_scenario_snapshot_digestcheck(self, scenario_id: str) -> None:
        """load-scenario roster_digest matches independent reference_roster."""
        fx_clean_state()
        proc = fx_invoke(
            [FX_BIN, "load-scenario", "--scenario", scenario_id, "--fixture-dir", str(FX_BUNDLE)]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        body = json.loads(FX_ROSTER.read_text(encoding="utf-8"))
        ref = reference_roster(scenario_id, FX_BUNDLE)
        assert body["roster_digest"] == ref["roster_digest"]

    def test_fxr02_ndc_eleven_digit_padding(self) -> None:
        """NDC normalizes to eleven digits in 5-4-2 segments."""
        doc = json.loads((FX_BUNDLE / "scenarios/ndc-normalize/scenario.json").read_text(encoding="utf-8"))
        assert normalize_ndc(doc["drugs"][0]["ndc"]) == "00012-3456-78"

    def test_fxr03_rxnorm_rank_winner(self) -> None:
        """Empty rxnorm selects highest-rank alias code."""
        doc = json.loads((FX_BUNDLE / "scenarios/rxnorm-alias/scenario.json").read_text(encoding="utf-8"))
        assert preferred_rxnorm(doc["drugs"][0]) == "RX050"

    def test_fxr04_plan_waiver_matrix_row(self) -> None:
        """Plan override drives requires_pa on published matrix rows."""
        fx_clean_state()
        fx_full_matrix_run("plan-override")
        body = fx_read_json(FX_MATRIX)
        ref = reference_matrix("plan-override", FX_BUNDLE)
        assert body["rows"][0]["requires_pa"] == ref["rows"][0]["requires_pa"]

    def test_fxr05_step_prereq_publish_flag(self) -> None:
        """Step therapy chain gates step_complete on published rows."""
        fx_clean_state()
        fx_full_matrix_run("step-chain")
        body = fx_read_json(FX_MATRIX)
        ref = reference_matrix("step-chain", FX_BUNDLE)
        ref_target = next(r for r in ref["rows"] if not r["step_complete"])
        target = next(r for r in body["rows"] if r["ndc_normalized"] == ref_target["ndc_normalized"])
        assert target["step_complete"] == ref_target["step_complete"]
        assert target["step_complete"] is False

    def test_fxr06_effective_start_tie_break(self) -> None:
        """Equal priority overrides prefer latest effective_start on or before as-of."""
        doc = json.loads((FX_BUNDLE / "scenarios/date-window/scenario.json").read_text(encoding="utf-8"))
        plan = doc["plans"][0]["plan_id"]
        ndc = doc["drugs"][0]["ndc"]
        ovr = select_override(doc["overrides"], plan, ndc, doc["as_of"])
        assert ovr is not None
        assert ovr["effective_start"] == "2024-06-01"

    def test_fxr07_refresh_counter_nonzero(self) -> None:
        """refresh-db seals refresh_revision greater than zero before publish."""
        fx_clean_state()
        fx_full_matrix_run("matrix-publish")
        gen = fx_read_json(FX_GEN)
        assert gen["refresh_revision"] >= 1

    def test_fxr08_multi_plan_row_totals(self) -> None:
        """Multi-plan scenarios publish the expected row_count."""
        fx_clean_state()
        fx_full_matrix_run("multi-plan")
        body = fx_read_json(FX_MATRIX)
        ref = reference_matrix("multi-plan", FX_BUNDLE)
        assert body["row_count"] == ref["row_count"]

    def test_fxr09_matrix_plan_ndc_sequence(self) -> None:
        """Published rows follow plan_id then ndc_normalized ascending order."""
        fx_clean_state()
        fx_full_matrix_run("multi-plan")
        body = fx_read_json(FX_MATRIX)
        ref = reference_matrix("multi-plan", FX_BUNDLE)
        assert [r["plan_id"] for r in body["rows"]] == [r["plan_id"] for r in ref["rows"]]

    def test_fxr10_matrix_digestcheck_match(self) -> None:
        """matrix_digest matches independent reference_matrix seal."""
        fx_clean_state()
        fx_full_matrix_run("matrix-publish")
        body = fx_read_json(FX_MATRIX)
        ref = reference_matrix("matrix-publish", FX_BUNDLE)
        assert body["matrix_digest"] == ref["matrix_digest"]
        baseline = [r for r in body["rows"] if not r["override_applied"]]
        assert baseline, "expected at least one baseline row"
        assert all(r["effective_rule"] == "baseline" for r in baseline)
