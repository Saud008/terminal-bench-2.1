"""emit-closure ledger tests."""

from __future__ import annotations

import json
from pathlib import Path

from rtbal_helpers import FIXTURES, RTBAL, pipeline, read_json, reset, run


class TestEmitClosure:
    def test_emit_blocked_without_run_id(self) -> None:
        """emit-closure must fail when run-balance has not set a positive run_id."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        out = Path("/app/output/blocked.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        proc = run(
            [str(RTBAL), "emit-closure", "--trial", trial_id, "--root", str(FIXTURES), "--out", str(out)]
        )
        assert proc.returncode != 0

    def test_closure_json_matches_reference(self) -> None:
        """imbalance closure JSON must match independent rtbal_refmath reference_pipeline output."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        out = pipeline(trial_id)
        closure = read_json(out)
        ref = __import__("rtbal_refmath").reference_pipeline(FIXTURES, trial_id)["closure"]
        assert closure == ref

    def test_closure_fingerprint_present(self) -> None:
        """closure fingerprint must be a 64-character hex digest per balance-closure-schema.md."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][2]["trial_id"]
        out = pipeline(trial_id)
        closure = read_json(out)
        assert len(closure["closure_digest"]) == 64

    def test_max_skew_is_absolute_arm_gap(self) -> None:
        """max_skew must equal the largest absolute active arm count gap across strata."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][3]["trial_id"]
        out = pipeline(trial_id)
        closure = read_json(out)
        ref = __import__("rtbal_refmath").reference_pipeline(FIXTURES, trial_id)["closure"]
        assert closure["max_skew"] == ref["max_skew"]


class TestDecoyModule:
    def test_sample_size_prior_decoy_off_hot_path(self) -> None:
        """decoy/sample_size_prior.rs must exist but not be required by compile-trial success."""
        decoy = FIXTURES.parent / "decoy" / "sample_size_prior.rs"
        assert decoy.is_file()
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        proc = run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        assert proc.returncode == 0
