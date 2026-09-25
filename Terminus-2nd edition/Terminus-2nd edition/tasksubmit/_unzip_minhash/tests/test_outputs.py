"""G-026 entrypoint — MinHash feature-dedup eval tests with minhash_ref reference."""

from __future__ import annotations

import json
import subprocess  # noqa: F401 — verifier drives minclus CLI through subprocess helpers

from minclus_run import run_pipeline, wipe
from minhash_ref import reference_report  # noqa: F401

import test_minclus_contract  # noqa: F401
import test_minclus_scan_cache  # noqa: F401
import test_minclus_tb3_traps  # noqa: F401

OUTPUT_DIR = "/app/output/"
SKETCH_INDEX_DIR = "/app/state/sketch-index/"


def test_feature_batch_eval_report_matches_reference():
    """Near-duplicate feature batch dedup eval report must match independent metric reference."""
    wipe()
    run_id = "run-ml-entry"
    out = run_pipeline(run_id, "near-duplicates-basic")
    rep = json.loads(out.read_text(encoding="utf-8"))
    from minclus_run import CORPUS_DIR

    ref = reference_report(run_id, CORPUS_DIR / "near-duplicates-basic")
    assert rep["audit_digest"] == ref["audit_digest"]
    assert rep["clusters"] == ref["clusters"]


def test_inference_sketch_index_schema_fields():
    """Feature embedding sketch index must record eval schema fields after batch scan."""
    wipe()
    run_id = "run-ml-sketch"
    run_pipeline(run_id, "unicode-punct-mix")
    from minclus_run import APP_ROOT

    sketch = json.loads(
        (APP_ROOT / "state" / "sketch-index" / f"{run_id}.json").read_text(encoding="utf-8")
    )
    assert sketch["scan_generation"] == 1
    assert sketch["documents"][0]["signature"]


def test_dedup_eval_metric_singleton_count():
    """Dedup eval report export must include singleton metric count for threshold batch."""
    wipe()
    run_id = "run-ml-metric"
    out = run_pipeline(run_id, "threshold-edge", floor=0.75)
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["singleton_count"] >= 2


def test_sketch_index_written_under_state_sketch_index_dir():
    """Feature sketch index JSON must be written under /app/state/sketch-index/ per schema."""
    wipe()
    run_id = "run-ml-state-path"
    run_pipeline(run_id, "near-duplicates-basic")
    from minclus_run import APP_ROOT

    sketch_path = APP_ROOT / "state" / "sketch-index" / f"{run_id}.json"
    assert str(sketch_path).startswith(SKETCH_INDEX_DIR)
    assert sketch_path.is_file()


def test_dedup_eval_report_written_under_app_output():
    """Dedup eval report JSON must be written under /app/output/ per provenance contract."""
    wipe()
    run_id = "run-ml-output-path"
    out = run_pipeline(run_id, "near-duplicates-basic")
    assert str(out).startswith(OUTPUT_DIR)
    assert out.is_file()
