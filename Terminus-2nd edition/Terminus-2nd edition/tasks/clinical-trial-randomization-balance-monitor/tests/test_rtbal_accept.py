"""accept-log normalization tests."""

from __future__ import annotations

import json

from rtbal_helpers import FIXTURES, LATCH, STAGING, RTBAL, reset, run
from rtbal_refmath import reference_pipeline


class TestAcceptLog:
    def test_accept_writes_chronicle_artifact(self) -> None:
        """accept-log must materialize /app/work/enrollment-chronicle.json after compile-trial."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        proc = run([str(RTBAL), "accept-log", "--trial", trial_id, "--root", str(FIXTURES)])
        assert proc.returncode == 0
        assert STAGING.is_file()

    def test_normalized_count_dedupes_replays(self) -> None:
        """normalized_count must drop duplicate subject seq replays per enrollment-chronicle-normalization.md."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][0]["trial_id"]
        run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        run([str(RTBAL), "accept-log", "--trial", trial_id, "--root", str(FIXTURES)])
        chronicle = json.loads(STAGING.read_text(encoding="utf-8"))
        ref = reference_pipeline(FIXTURES, trial_id)["chronicle"]
        assert chronicle["normalized_count"] == ref["normalized_count"]

    def test_rows_sorted_ts_then_seq(self) -> None:
        """Chronicle rows must sort by ts then seq as required by enrollment-chronicle-normalization.md."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][2]["trial_id"]
        run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        run([str(RTBAL), "accept-log", "--trial", trial_id, "--root", str(FIXTURES)])
        chronicle = json.loads(STAGING.read_text(encoding="utf-8"))
        rows = chronicle["rows"]
        keys = [(r["ts"], r["seq"]) for r in rows]
        assert keys == sorted(keys)

    def test_chronicle_carries_manifest_fingerprint(self) -> None:
        """Chronicle artifact must carry trial_id and manifest fingerprint from the manifest latch."""
        reset()
        catalog = json.loads((FIXTURES / "trial_catalog.json").read_text(encoding="utf-8"))
        trial_id = catalog["trials"][1]["trial_id"]
        run([str(RTBAL), "compile-trial", "--trial", trial_id, "--root", str(FIXTURES)])
        run([str(RTBAL), "accept-log", "--trial", trial_id, "--root", str(FIXTURES)])
        chronicle = json.loads(STAGING.read_text(encoding="utf-8"))
        latch = json.loads(LATCH.read_text(encoding="utf-8"))
        assert chronicle["trial_id"] == trial_id
        assert chronicle["protocol_digest"] == latch["protocol_digest"]
