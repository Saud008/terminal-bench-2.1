"""run-balance stratification and cap tests."""

from __future__ import annotations

import json

from rtbal_helpers import BALANCE, FIXTURES, RTBAL, pipeline, read_json, reset, run
from rtbal_refmath import reference_pipeline


class TestRunBalance:
    def test_run_balance_sets_run_id(self) -> None:
        """run-balance must persist a positive run_id in /app/work/balance-run.json."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        run([str(RTBAL), "accept-log", "--trial", trial_id, "--root", str(FIXTURES)])
        proc = run([str(RTBAL), "run-balance", "--trial", trial_id, "--root", str(FIXTURES)])
        assert proc.returncode == 0
        balance = read_json(BALANCE)
        assert balance["run_id"] > 0

    def test_per_stratum_active_counts_reference(self) -> None:
        """per_stratum active arm counts must match stratified-block-randomization reference math."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][1]["trial_id"]
        pipeline(trial_id)
        balance = read_json(BALANCE)
        ref = reference_pipeline(FIXTURES, trial_id)["balance"]
        assert balance["per_stratum"] == ref["per_stratum"]

    def test_withdrawn_excluded_from_active_balance(self) -> None:
        """Withdrawn subjects must not affect active max_skew per site-cap-active-policy.md."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][1]["trial_id"]
        pipeline(trial_id)
        balance = read_json(BALANCE)
        ref = reference_pipeline(FIXTURES, trial_id)["balance"]
        assert balance["max_skew"] == ref["max_skew"]

    def test_incomplete_slot_remaining(self) -> None:
        """open_slots must report unfilled slots in the current permuted arm lattice."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        pipeline(trial_id)
        balance = read_json(BALANCE)
        ref = reference_pipeline(FIXTURES, trial_id)["balance"]
        assert balance["open_slots"] == ref["open_slots"]

    def test_venue_cap_sorted(self) -> None:
        """venues_at_cap must list capped venues in lexicographic sorted order."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][2]["trial_id"]
        pipeline(trial_id)
        balance = read_json(BALANCE)
        venues = balance["venues_at_cap"]
        assert venues == sorted(venues)
