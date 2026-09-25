"""Hidden verifier-only witness bundles."""

from __future__ import annotations

import json

from conftest import EDGE_BUNDLE, LEDGER_PATH, STAGE_PATH, TB3_BUNDLE, VERDICT_PATH
from tw1_independent_math import golden_quorum_at_epoch


def test_tb3_fork_provenance_meets_quorum(isolated_bundle, twctl):
    """tb3-bundle forked provenance from tw01 meets quorum at verification round 40."""
    meta = isolated_bundle(TB3_BUNDLE)
    twctl.full_cycle(meta, 40)
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    assert ledger["quorum_met"] is True
    assert ledger["valid_witness_count"] == 2
    tw03 = next(r for r in ledger["witnesses"] if r["witness_id"] == "tw03")
    assert tw03["counts_toward_quorum"] is False


def test_tb3_signer_revocation_at_epoch_40(isolated_bundle, twctl, stage_reader):
    """tb3-c revocation round 37 affects round 40 evaluation."""
    meta = isolated_bundle(TB3_BUNDLE)
    twctl.load_bundle(meta)
    twctl.check_epoch(40)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    staging = stage_reader(STAGE_PATH)
    ref = golden_quorum_at_epoch(staging, 40)
    tw03 = next(w for w in got["witnesses"] if w["witness_id"] == "tw03")
    assert tw03["revoked_signer"] == ref["witnesses"][2]["revoked_signer"]


def test_tb3_epoch_bias_env_shifts_verdict(isolated_bundle, twctl, stage_reader):
    """TB3_EPOCH_BIAS offsets effective verification round."""
    meta = isolated_bundle(TB3_BUNDLE)
    twctl.wipe_outputs()
    twctl.load_bundle(meta)
    bias = 2
    twctl.check_epoch(36, env={"TB3_EPOCH_BIAS": str(bias)})
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    staging = stage_reader(STAGE_PATH)
    ref = golden_quorum_at_epoch(staging, 36 + bias)
    assert got == ref
    assert got["epoch"] == 38
    tw03 = next(w for w in got["witnesses"] if w["witness_id"] == "tw03")
    assert tw03["revoked_signer"] is True


def test_revoke_edge_bundle_fails_quorum_at_100(isolated_bundle, twctl):
    """revoke-edge-bundle fails quorum when edge-a revoked at round 100."""
    meta = isolated_bundle(EDGE_BUNDLE)
    twctl.full_cycle(meta, 100)
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    assert ledger["quorum_met"] is False
    assert ledger["valid_witness_count"] == 1
