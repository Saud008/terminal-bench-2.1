"""Sealed release witness ledger export."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from conftest import ALPHA_BUNDLE, LEDGER_PATH, STAGE_PATH, VERDICT_PATH
from tw1_independent_math import golden_quorum_at_epoch, golden_release_ledger


def test_emit_writes_release_witness_ledger(twctl):
    """emit writes /app/output/release-witness-ledger.json."""
    twctl.full_cycle(ALPHA_BUNDLE, 45)
    assert LEDGER_PATH.is_file()
    assert str(LEDGER_PATH) == "/app/output/release-witness-ledger.json"


def test_export_body_matches_golden_ledger(twctl, stage_reader):
    """ledger-export-schema.md body matches independent golden."""
    twctl.full_cycle(ALPHA_BUNDLE, 45)
    staging = stage_reader(STAGE_PATH)
    verdict = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    got = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    ref = golden_release_ledger(staging, verdict)
    assert got == ref


def test_ledger_digest_uses_artifact_not_bundle_path(twctl, stage_reader):
    """ledger_digest binds artifact_digest bytes, not bundle_dir."""
    twctl.full_cycle(ALPHA_BUNDLE, 45)
    got = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    staging = stage_reader(STAGE_PATH)
    verdict = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    ref = golden_release_ledger(staging, verdict)
    assert got["ledger_digest"] == ref["ledger_digest"]
    assert len(got["ledger_digest"]) == 64
    wrong = hashlib.sha256(staging["bundle_dir"].encode()).hexdigest()
    assert got["ledger_digest"] != wrong


def test_export_rows_sorted_by_witness_id(twctl):
    """ledger export sorts witnesses by witness_id ascending."""
    twctl.full_cycle(ALPHA_BUNDLE, 45)
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    ids = [r["witness_id"] for r in ledger["witnesses"]]
    assert ids == sorted(ids)


def test_subprocess_pipeline_agrees_with_golden(twctl, stage_reader):
    """Full load check emit cycle matches golden quorum math."""
    twctl.full_cycle(ALPHA_BUNDLE, 45)
    staging = stage_reader(STAGE_PATH)
    verdict = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    ref_check = golden_quorum_at_epoch(staging, 45)
    assert verdict == ref_check


def test_release_alpha_end_to_end_contract(twctl):
    """Instruction bundle path exercised through sealed export."""
    twctl.full_cycle(ALPHA_BUNDLE, 45)
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    assert ledger["quorum_met"] is True
    assert ledger["release_id"] == "app-v2.4.0"


def test_emit_uses_staged_snapshot_not_bundle_witness_json(isolated_bundle, twctl, stage_reader):
    """emit reads staging + verdict only; never re-reads bundle witness JSON."""
    meta = isolated_bundle(ALPHA_BUNDLE)
    twctl.load_bundle(meta)
    staging_before = stage_reader(STAGE_PATH)
    witness_dir = Path(meta) / "witnesses"
    for path in witness_dir.glob("*.json"):
        path.unlink()
    # Corrupt remaining bundle surface so any re-read would fail or diverge.
    shutil.rmtree(witness_dir)
    witness_dir.mkdir()
    (witness_dir / "bogus.json").write_text('{"witness_id":"bogus"}\n', encoding="utf-8")

    twctl.check_epoch(45)
    twctl.emit_ledger()

    staging = stage_reader(STAGE_PATH)
    assert staging["witnesses"] == staging_before["witnesses"]
    verdict = json.loads(VERDICT_PATH.read_text(encoding="utf-8"))
    got = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    assert [r["witness_id"] for r in got["witnesses"]] == sorted(
        w["witness_id"] for w in staging["witnesses"]
    )
    assert all(row["witness_id"] != "bogus" for row in got["witnesses"])
    assert got == golden_release_ledger(staging, verdict)
