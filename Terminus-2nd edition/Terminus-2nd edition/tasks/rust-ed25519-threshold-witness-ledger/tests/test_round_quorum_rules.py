"""Quorum evaluation and signer revocation rounds."""

from __future__ import annotations

import json
import shutil

from conftest import ALPHA_BUNDLE, ALT_STAGE_PATH, STAGE_PATH, VERDICT_PATH
from tw1_independent_math import golden_quorum_at_epoch


def test_check_persists_quorum_verdict_round(twctl, stage_reader):
    """check writes quorum-verdict.json including verification round."""
    twctl.load_bundle(ALPHA_BUNDLE)
    twctl.check_epoch(45)
    assert VERDICT_PATH.is_file()
    data = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    assert data["epoch"] == 45


def test_check_honors_staging_path_flag(twctl, stage_reader):
    """check --staging <path> evaluates the caller-provided snapshot."""
    twctl.load_bundle(ALPHA_BUNDLE)
    shutil.copyfile(STAGE_PATH, ALT_STAGE_PATH)
    STAGE_PATH.write_text('{"witnesses":[]}\n', encoding="utf-8")
    twctl.check_epoch(45, staging=ALT_STAGE_PATH)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    staging = stage_reader(ALT_STAGE_PATH)
    ref = golden_quorum_at_epoch(staging, 45)
    assert got == ref
    assert got["quorum_met"] is True
    assert len(got["witnesses"]) == 4


def test_alpha_quorum_satisfied_at_round_45(twctl, stage_reader):
    """Bundled witnesses meet threshold at verification round 45."""
    twctl.load_bundle(ALPHA_BUNDLE)
    twctl.check_epoch(45)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    staging = stage_reader(STAGE_PATH)
    ref = golden_quorum_at_epoch(staging, 45)
    assert got["quorum_met"] == ref["quorum_met"]
    assert got["quorum_met"] is True
    # Four witness rows, three distinct signers (w002 and w004 share key-b).
    assert got["valid_witness_count"] == 3


def test_revocation_excludes_key_c_at_round_55(twctl, stage_reader):
    """revocation-epochs.md excludes key-c at verification round 55."""
    twctl.load_bundle(ALPHA_BUNDLE)
    twctl.check_epoch(55)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    staging = stage_reader(STAGE_PATH)
    ref = golden_quorum_at_epoch(staging, 55)
    assert got == ref
    w003 = next(w for w in got["witnesses"] if w["witness_id"] == "w003")
    assert w003["revoked_signer"] is True
    assert w003["counts_toward_quorum"] is False


def test_per_witness_outcomes_match_golden(twctl, stage_reader):
    """canonical-message-binding.md signature outcomes match golden math."""
    twctl.load_bundle(ALPHA_BUNDLE)
    twctl.check_epoch(45)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    staging = stage_reader(STAGE_PATH)
    ref = golden_quorum_at_epoch(staging, 45)
    assert got["witnesses"] == ref["witnesses"]


def test_w002_provenance_chain_valid(twctl, stage_reader):
    """witness-provenance.md validates prior chain for w002."""
    twctl.load_bundle(ALPHA_BUNDLE)
    twctl.check_epoch(45)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    w002 = next(w for w in got["witnesses"] if w["witness_id"] == "w002")
    assert w002["provenance_ok"] is True


def test_distinct_signer_keys_count_once(twctl, stage_reader):
    """quorum-policy.md counts each signer_keyid at most once."""
    twctl.load_bundle(ALPHA_BUNDLE)
    twctl.check_epoch(45)
    verify = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    staging = stage_reader(STAGE_PATH)
    signers = {w["signer_keyid"] for w in staging["witnesses"]}
    assert len(staging["witnesses"]) == 4
    assert len(signers) == 3
    assert verify["valid_witness_count"] <= len(signers)
    assert verify["valid_witness_count"] == 3


def _rewrite_staging_priors(staging: dict, mutations: dict[str, str | None]) -> dict:
    rows = []
    for row in staging["witnesses"]:
        copy = dict(row)
        if copy["witness_id"] in mutations:
            copy["prior_witness_id"] = mutations[copy["witness_id"]]
        rows.append(copy)
    out = dict(staging)
    out["witnesses"] = rows
    return out


def test_provenance_missing_prior_id_fails(twctl, stage_reader):
    """Missing prior_witness_id targets fail provenance_ok."""
    twctl.load_bundle(ALPHA_BUNDLE)
    staging = stage_reader(STAGE_PATH)
    mutated = _rewrite_staging_priors(staging, {"w002": "does-not-exist"})
    STAGE_PATH.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    twctl.check_epoch(45)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    ref = golden_quorum_at_epoch(mutated, 45)
    w002 = next(w for w in got["witnesses"] if w["witness_id"] == "w002")
    ref_w002 = next(w for w in ref["witnesses"] if w["witness_id"] == "w002")
    assert ref_w002["provenance_ok"] is False
    assert w002["provenance_ok"] is False
    assert got["provenance_ok"] is False
    assert got["quorum_met"] is False


def test_provenance_cycle_fails(twctl, stage_reader):
    """Cyclic prior_witness_id edges fail provenance validation."""
    twctl.load_bundle(ALPHA_BUNDLE)
    staging = stage_reader(STAGE_PATH)
    mutated = _rewrite_staging_priors(staging, {"w001": "w002", "w002": "w001"})
    STAGE_PATH.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    twctl.check_epoch(45)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    ref = golden_quorum_at_epoch(mutated, 45)
    assert ref["provenance_ok"] is False
    assert got["provenance_ok"] is False
    assert got["quorum_met"] is False
    w001 = next(w for w in got["witnesses"] if w["witness_id"] == "w001")
    w002 = next(w for w in got["witnesses"] if w["witness_id"] == "w002")
    assert w001["provenance_ok"] is False or w002["provenance_ok"] is False


def test_provenance_prior_epoch_ge_current_fails(twctl, stage_reader):
    """Prior epochs greater than or equal to the current witness epoch fail."""
    twctl.load_bundle(ALPHA_BUNDLE)
    staging = stage_reader(STAGE_PATH)
    # w002 epoch 20; point at w003 (epoch 40) so prior epoch is strictly greater.
    mutated = _rewrite_staging_priors(staging, {"w002": "w003"})
    STAGE_PATH.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    twctl.check_epoch(45)
    got = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    ref = golden_quorum_at_epoch(mutated, 45)
    w002 = next(w for w in got["witnesses"] if w["witness_id"] == "w002")
    ref_w002 = next(w for w in ref["witnesses"] if w["witness_id"] == "w002")
    assert ref_w002["provenance_ok"] is False
    assert w002["provenance_ok"] is False
    assert got["provenance_ok"] is False
    assert got["quorum_met"] is False

    # Equal-epoch prior: force w002.epoch == w004.epoch and set w004.prior = w002.
    equal = dict(staging)
    equal_rows = [dict(r) for r in staging["witnesses"]]
    w002_row = next(r for r in equal_rows if r["witness_id"] == "w002")
    w004_row = next(r for r in equal_rows if r["witness_id"] == "w004")
    w002_row["epoch"] = w004_row["epoch"]
    w004_row["prior_witness_id"] = "w002"
    equal["witnesses"] = equal_rows
    STAGE_PATH.write_text(json.dumps(equal, indent=2) + "\n", encoding="utf-8")
    twctl.check_epoch(45)
    got_eq = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    ref_eq = golden_quorum_at_epoch(equal, 45)
    w004_out = next(w for w in got_eq["witnesses"] if w["witness_id"] == "w004")
    ref_w004 = next(w for w in ref_eq["witnesses"] if w["witness_id"] == "w004")
    assert ref_w004["provenance_ok"] is False
    assert w004_out["provenance_ok"] is False
    assert got_eq["provenance_ok"] is False
