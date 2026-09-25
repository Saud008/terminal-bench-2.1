"""Contract math parity checks."""

from __future__ import annotations

import json

import pytest
from mlprov_cli_support import (
    FIXTURE_DIR,
    SEED_POOL,
    run_curator,
    wipe,
)
from mlprov_contract_math import reference_curate, reference_load_scenario


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_metric_order_matches_contract_math():
    """Exported metric_epochs must match the documented epoch, step, and key ordering contract."""
    seed = SEED_POOL[0]
    out = run_curator(seed, "metric-epoch-order")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "metric-epoch-order.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["metric_epochs"] == ref["metric_epochs"]



def test_metric_order_flag_matches_contract_math():
    """The epoch_monotonic_ok summary flag must follow the reference metric ordering rules."""
    seed = SEED_POOL[2]
    out = run_curator(seed, "metric-epoch-order")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "metric-epoch-order.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["summary"]["epoch_monotonic_ok"] == ref["summary"]["epoch_monotonic_ok"]



def test_artifact_hashes_match_contract_math():
    """Artifact digests must hash normalized rel_path plus content exactly like the contract math."""
    seed = SEED_POOL[0]
    out = run_curator(seed, "artifact-digest-tree")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "artifact-digest-tree.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["artifact_digests"] == ref["artifact_digests"]



def test_artifact_paths_drop_dot_slash_prefix():
    """Artifact rel_path values must be normalized before export so they never keep a leading ./ prefix."""
    seed = SEED_POOL[1]
    out = run_curator(seed, "artifact-digest-tree")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "artifact-digest-tree.json", seed)
    ref = reference_curate(sc, seed)
    assert [a["rel_path"] for a in rep["artifact_digests"]] == [a["rel_path"] for a in ref["artifact_digests"]]
    assert all(not p.startswith("./") for p in [a["rel_path"] for a in rep["artifact_digests"]])



def test_pin_bindings_match_contract_math():
    """Dataset binding rows must match manifest version-hash validation from the contract math."""
    seed = SEED_POOL[0]
    out = run_curator(seed, "basic-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "basic-lineage.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["dataset_bindings"] == ref["dataset_bindings"]
    assert rep["summary"]["binding_ok"] == ref["summary"]["binding_ok"]



def test_pin_mismatch_marks_binding_false():
    """A dataset pin mismatch must clear the exported binding_ok summary flag."""
    seed = SEED_POOL[1]
    out = run_curator(seed, "dataset-pin-mismatch")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "dataset-pin-mismatch.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["summary"]["binding_ok"] == ref["summary"]["binding_ok"]



def test_audit_digest_matches_contract_math():
    """audit_digest must match the canonical summary hash defined by the export contract."""
    seed = SEED_POOL[0]
    out = run_curator(seed, "basic-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "basic-lineage.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["audit_digest"] == ref["audit_digest"]



def test_summary_written_under_app_output():
    """export summary must write the requested report file under /app/output/"""
    seed = SEED_POOL[0]
    out = run_curator(seed, "basic-lineage")
    assert out.is_file()
    assert str(out).startswith("/app/output/")


