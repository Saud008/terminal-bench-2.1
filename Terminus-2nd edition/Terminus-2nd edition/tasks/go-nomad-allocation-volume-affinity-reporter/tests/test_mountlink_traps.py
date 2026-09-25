"""Hidden mountlink and stale traps for nomrep — distinct failure modes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from placement_atlas_math import reference_compile_atlas, reference_load_scenario
from nomrep_atlas_cli import SEED_POOL, run_full_atlas, wipe

HIDDEN_DIR = Path("/opt/verifier-fixtures/scenarios")


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_trap_namespace_salt_shifts_mountlink_key():
    """TB3_NAMESPACE_SALT must affect volume_key without breaking join_ok."""
    seed = SEED_POOL[0]
    env = {"TB3_NAMESPACE_SALT": "-edge"}
    out = run_full_atlas(
        seed,
        "hidden-csi-namespace-join",
        fixture_dir=HIDDEN_DIR,
        env=env,
    )
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(HIDDEN_DIR / "hidden-csi-namespace-join.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["volume_joins"] == ref["volume_joins"]
    assert rep["volume_joins"][0]["volume_key"] == "infra/vol-secrets-edge"


def test_trap_modify_index_stale_beats_high_create_index():
    """Stale filter must use modify_index so high create_index rows still suppress."""
    seed = SEED_POOL[1]
    out = run_full_atlas(
        seed,
        "hidden-modify-index-stale",
        fixture_dir=HIDDEN_DIR,
    )
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(HIDDEN_DIR / "hidden-modify-index-stale.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["summary"]["stale_suppressed"] == ref["summary"]["stale_suppressed"]
    assert rep["summary"]["active_alloc_count"] == 1
    assert rep["summary"]["stale_suppressed"] == 1


def test_trap_audit_body_includes_salted_mountlink_keys():
    """Hidden namespace salt must flow into audit_digest volume_keys ordering."""
    seed = SEED_POOL[2]
    env = {"TB3_NAMESPACE_SALT": "-edge"}
    out = run_full_atlas(
        seed,
        "hidden-csi-namespace-join",
        fixture_dir=HIDDEN_DIR,
        env=env,
    )
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(HIDDEN_DIR / "hidden-csi-namespace-join.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert rep["audit_digest"] == ref["audit_digest"]
