"""compile-trial tests for rtbalctl."""

from __future__ import annotations

import json

from rtbal_helpers import FIXTURES, LATCH, RTBAL, reset, run
from rtbal_refmath import protocol_digest


class TestCompileTrial:
    def test_compile_writes_manifest_latch_file(self) -> None:
        """compile-trial must write /app/state/trial-latch.json per trial-latch-schema.md."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        proc = run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert LATCH.is_file()

    def test_manifest_fingerprint_matches_reference(self) -> None:
        """manifest fingerprint must match deterministic preimage rank ladder in trial-latch-schema.md."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        proc = run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        assert proc.returncode == 0
        latch = json.loads(LATCH.read_text(encoding="utf-8"))
        protocol = json.loads((FIXTURES / "trials" / f"{trial_id}.json").read_text(encoding="utf-8"))
        assert latch["protocol_digest"] == protocol_digest(protocol)

    def test_latch_excludes_enrollment_bodies(self) -> None:
        """Latch metadata must not embed enrollment row bodies from the NDJSON chronicle."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][1]["trial_id"]
        run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        latch = json.loads(LATCH.read_text(encoding="utf-8"))
        assert "rows" not in latch
        assert latch["log_relpath"] == f"logs/{trial_id}.ndjson"

    def test_compile_requires_trial_flag(self) -> None:
        """compile-trial must reject invocations missing the required --trial flag."""
        reset()
        proc = run([str(RTBAL), "compile-trial", "--root", str(FIXTURES)])
        assert proc.returncode != 0
