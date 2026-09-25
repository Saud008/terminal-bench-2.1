"""Compile and placement behavioral tests for nomrep."""

from __future__ import annotations

import json

import pytest

from placement_atlas_math import reference_compile_atlas, reference_load_scenario
from nomrep_atlas_cli import FIXTURE_DIR, SEED_POOL, run_full_atlas, wipe


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_mountlink_rows_follow_namespace_key_contract():
    """Mountlink rows must use namespace/volume_id keys per csi-mountlink-contract.md."""
    seed = SEED_POOL[0]
    out = run_full_atlas(seed, "basic-volume-join")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "basic-volume-join.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["volume_joins"] == ref["volume_joins"]
    assert rep["volume_joins"][0]["volume_key"] == "prod/vol-cache-a"
    assert rep["volume_joins"][0]["join_ok"] is True


def test_node_class_hard_gate_before_soft_rank():
    """Placements must drop failing hard constraints before affinity ranking."""
    seed = SEED_POOL[1]
    out = run_full_atlas(seed, "node-class-precedence")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "node-class-precedence.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["placements"] == ref["placements"]
    assert all(p["node_class"] == "gpu" for p in rep["placements"])
    assert len(rep["placements"]) == 2


def test_reschedule_aggregate_honors_failed_flag():
    """Reschedule total must sum failed attempts only per reschedule-stale-policy.md."""
    seed = SEED_POOL[2]
    out = run_full_atlas(seed, "reschedule-attempt-chain")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "reschedule-attempt-chain.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["summary"]["reschedule_total"] == ref["summary"]["reschedule_total"]
    assert rep["summary"]["reschedule_total"] == 2


def test_stale_gate_uses_modify_index_floor():
    """Stale suppression must honor modify_index cutoff and superseded_by."""
    seed = SEED_POOL[3]
    out = run_full_atlas(seed, "stale-allocation-filter")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "stale-allocation-filter.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["summary"]["stale_suppressed"] == ref["summary"]["stale_suppressed"]
    assert rep["summary"]["active_alloc_count"] == 1


def test_drain_gate_excludes_desired_stop_before_stale():
    """Drain eligibility must exclude desired_status stop rows per drain-eligibility.md."""
    seed = SEED_POOL[3]
    out = run_full_atlas(seed, "stale-allocation-filter")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "stale-allocation-filter.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["summary"]["drain_excluded"] == ref["summary"]["drain_excluded"]
    assert rep["summary"]["drain_excluded"] >= 1


def test_spread_penalty_uses_node_id_not_class():
    """Spread penalty must count co-located node_id peers per spread-topology.md."""
    seed = SEED_POOL[4]
    out = run_full_atlas(seed, "affinity-soft-rank")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "affinity-soft-rank.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["placements"] == ref["placements"]
    assert rep["summary"]["spread_penalty_total"] == ref["summary"]["spread_penalty_total"]
    assert rep["summary"]["affinity_monotone_ok"] is True


def test_audit_fingerprint_matches_canonical_publish_body():
    """audit_digest must match publish-atlas-fields.md canonical body."""
    seed = SEED_POOL[0]
    out = run_full_atlas(seed, "basic-volume-join")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "basic-volume-join.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["audit_digest"] == ref["audit_digest"]


def test_constraint_pass_flag_reflects_active_hard_rules():
    """Summary constraint_pass_ok reflects active allocation hard constraint state."""
    seed = SEED_POOL[1]
    out = run_full_atlas(seed, "node-class-precedence")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "node-class-precedence.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["summary"]["constraint_pass_ok"] == ref["summary"]["constraint_pass_ok"]


def test_mountlink_count_tracks_join_row_length():
    """Summary volume_join_count must equal volume_joins row count."""
    seed = SEED_POOL[2]
    out = run_full_atlas(seed, "basic-volume-join")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["summary"]["volume_join_count"] == len(rep["volume_joins"])


def test_focus_alloc_echoes_buffer_scope():
    """Published atlas must include scoped focus_alloc_id from buffer."""
    seed = SEED_POOL[0]
    out = run_full_atlas(seed, "affinity-soft-rank")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "affinity-soft-rank.json", seed)
    assert rep["focus_alloc_id"] == sc["focus_alloc_id"]


def test_later_scenario_replaces_journal_for_same_seed():
    """Later compile for same seed replaces prior active row per atlas-index-schema.md."""
    seed = SEED_POOL[4]
    run_full_atlas(seed, "basic-volume-join")
    out2 = run_full_atlas(seed, "reschedule-attempt-chain")
    rep2 = json.loads(out2.read_text(encoding="utf-8"))
    assert rep2["scenario"] == "reschedule-attempt-chain"


def test_placement_ranks_begin_at_one_ascending():
    """Placement rows must carry ranks starting at 1 in ascending order."""
    seed = SEED_POOL[3]
    out = run_full_atlas(seed, "affinity-soft-rank")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ranks = [p["placement_rank"] for p in rep["placements"]]
    assert ranks == sorted(ranks)
    if ranks:
        assert ranks[0] == 1
