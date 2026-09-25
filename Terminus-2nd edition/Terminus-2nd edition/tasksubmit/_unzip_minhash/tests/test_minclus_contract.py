"""Bundled MinHash dedup eval contract tests for feature embedding batches."""

from __future__ import annotations

import json

import pytest

from minclus_run import CORPUS_DIR, run_pipeline, wipe
from minhash_ref import reference_report


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


class TestMinclusContracts:
    def test_near_duplicates_basic_matches_reference(self):
        """Near duplicate batch must cluster per independent MinHash feature eval reference."""
        run_id = "run-near-basic"
        out = run_pipeline(run_id, "near-duplicates-basic")
        rep = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_report(run_id, CORPUS_DIR / "near-duplicates-basic")
        assert rep["cluster_run_id"] == ref["cluster_run_id"]
        assert rep["clusters"] == ref["clusters"]
        assert rep["audit_digest"] == ref["audit_digest"]
        assert rep["total_documents"] == ref["total_documents"]
        assert rep["singleton_count"] == ref["singleton_count"]

    def test_unicode_punct_normalization_pair(self):
        """NFKC normalization must merge unicode-punct-mix near duplicate pair."""
        run_id = "run-unicode"
        out = run_pipeline(run_id, "unicode-punct-mix")
        rep = json.loads(out.read_text(encoding="utf-8"))
        merged = next(c for c in rep["clusters"] if len(c["member_doc_ids"]) >= 2)
        assert set(merged["member_doc_ids"]) == {"u1", "u2"}

    def test_shingle_boundary_singleton_extra_token(self):
        """Shingle boundary corpus keeps non-overlapping docs separate."""
        run_id = "run-shingle"
        out = run_pipeline(run_id, "shingle-boundary", floor=0.5)
        rep = json.loads(out.read_text(encoding="utf-8"))
        assert rep["cluster_count"] >= 2

    def test_threshold_edge_respects_floor(self):
        """Threshold edge batch must not over-merge below jaccard eval metric floor."""
        run_id = "run-thresh"
        out = run_pipeline(run_id, "threshold-edge", floor=0.75)
        rep = json.loads(out.read_text(encoding="utf-8"))
        assert rep["singleton_count"] >= 2

    def test_multi_cluster_two_groups_plus_singleton(self):
        """Multi-cluster corpus yields two multi-member clusters and one singleton."""
        run_id = "run-multi"
        out = run_pipeline(run_id, "multi-cluster")
        rep = json.loads(out.read_text(encoding="utf-8"))
        sizes = sorted(len(c["member_doc_ids"]) for c in rep["clusters"])
        assert sizes[-1] >= 2
        assert rep["singleton_count"] >= 1

    def test_representative_is_lexicographic_minimum(self):
        """Cluster representative must be lexicographically smallest member doc_id."""
        run_id = "run-rep"
        out = run_pipeline(run_id, "multi-cluster")
        rep = json.loads(out.read_text(encoding="utf-8"))
        for cluster in rep["clusters"]:
            assert cluster["representative_doc_id"] == min(cluster["member_doc_ids"])

    def test_cluster_rows_sorted_by_cluster_id(self):
        """Dedup eval report clusters must sort by cluster_id ascending."""
        run_id = "run-sort"
        out = run_pipeline(run_id, "multi-cluster")
        rep = json.loads(out.read_text(encoding="utf-8"))
        ids = [c["cluster_id"] for c in rep["clusters"]]
        assert ids == sorted(ids)

    def test_decoy_module_not_on_hot_path(self):
        """Decoy lsh telemetry must not be required for scan group attest."""
        run_id = "run-decoy"
        out = run_pipeline(run_id, "near-duplicates-basic")
        assert out.exists()

    def test_member_doc_ids_sorted_in_export(self):
        """Each cluster member_doc_ids list must be sorted ascending."""
        run_id = "run-members"
        out = run_pipeline(run_id, "multi-cluster")
        rep = json.loads(out.read_text(encoding="utf-8"))
        for cluster in rep["clusters"]:
            assert cluster["member_doc_ids"] == sorted(cluster["member_doc_ids"])

    def test_sketch_staging_snapshot_generation_recorded(self):
        """First scan must record scan_generation one in sketch staging snapshot index."""
        run_id = "run-sketch-gen"
        run_pipeline(run_id, "near-duplicates-basic")
        sketch = json.loads(
            (
                CORPUS_DIR.parent.parent
                / "state"
                / "sketch-index"
                / f"{run_id}.json"
            ).read_text(encoding="utf-8")
        )
        assert sketch["scan_generation"] == 1

    def test_config_fingerprint_present(self):
        """Sketch index must include config_fingerprint from active config."""
        run_id = "run-cfg"
        run_pipeline(run_id, "near-duplicates-basic")
        sketch = json.loads(
            (
                CORPUS_DIR.parent.parent
                / "state"
                / "sketch-index"
                / f"{run_id}.json"
            ).read_text(encoding="utf-8")
        )
        ref = reference_report(run_id, CORPUS_DIR / "near-duplicates-basic")
        assert sketch["config_fingerprint"] == ref["config_fingerprint"]

    def test_group_generation_increments(self):
        """Regroup must increment group_generation in cluster graph."""
        from minclus_run import CLI_BIN, invoke

        run_id = "run-grp-gen"
        run_pipeline(run_id, "near-duplicates-basic")
        invoke([str(CLI_BIN), "group", "--run-id", run_id, "--jaccard-floor", "0.5"])
        graph = json.loads(
            (
                CORPUS_DIR.parent.parent
                / "work"
                / "cluster-graph"
                / f"{run_id}.json"
            ).read_text(encoding="utf-8")
        )
        assert graph["group_generation"] >= 2

    def test_sketch_index_file_written_to_state_path(self):
        """scan must write sketch index JSON under /app/state/sketch-index/."""
        run_id = "run-sketch-path"
        run_pipeline(run_id, "near-duplicates-basic")
        sketch_path = CORPUS_DIR.parent.parent / "state" / "sketch-index" / f"{run_id}.json"
        assert sketch_path.is_file()
        payload = json.loads(sketch_path.read_text(encoding="utf-8"))
        assert payload["run_id"] == run_id
        assert payload["documents"]

    def test_provenance_export_paths_under_output(self):
        """attest export must write provenance JSON under /app/output/."""
        run_id = "run-export-path"
        out = run_pipeline(run_id, "near-duplicates-basic")
        assert str(out).startswith("/app/output/")
        assert out.name.endswith("-provenance.json")
