"""Feature sketch scan generation and batch rescan eval tests."""

from __future__ import annotations

import json

import pytest

from minclus_run import CLI_BIN, CORPUS_DIR, invoke, run_pipeline, wipe


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


class TestScanCache:
    def test_rescan_increments_scan_generation(self):
        """Rescan of same batch run id must increment scan_generation in feature index schema."""
        run_id = "run-rescan"
        run_pipeline(run_id, "near-duplicates-basic")
        invoke(
            [
                str(CLI_BIN),
                "scan",
                "--corpus-dir",
                str(CORPUS_DIR / "near-duplicates-basic"),
                "--run-id",
                run_id,
                "--profile",
                "default",
            ]
        )
        sketch = json.loads(
            (
                CORPUS_DIR.parent.parent
                / "state"
                / "sketch-index"
                / f"{run_id}.json"
            ).read_text(encoding="utf-8")
        )
        assert sketch["scan_generation"] == 2

    def test_rescan_changes_cluster_run_id_after_regroup(self):
        """Rescan plus regroup must change cluster_run_id in provenance."""
        run_id = "run-reconcile"
        run_pipeline(run_id, "near-duplicates-basic")
        first = json.loads(
            (
                CORPUS_DIR.parent.parent
                / "output"
                / f"{run_id}-provenance.json"
            ).read_text(encoding="utf-8")
        )["cluster_run_id"]
        invoke(
            [
                str(CLI_BIN),
                "scan",
                "--corpus-dir",
                str(CORPUS_DIR / "near-duplicates-basic"),
                "--run-id",
                run_id,
                "--profile",
                "default",
            ]
        )
        invoke([str(CLI_BIN), "group", "--run-id", run_id, "--jaccard-floor", "0.5"])
        out = CORPUS_DIR.parent.parent / "output" / f"{run_id}-provenance.json"
        invoke([str(CLI_BIN), "attest", "--run-id", run_id, "--output", str(out)])
        second = json.loads(out.read_text(encoding="utf-8"))["cluster_run_id"]
        assert second != first
