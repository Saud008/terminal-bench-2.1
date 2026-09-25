"""Load and staging snapshot behavior."""

from __future__ import annotations

from pathlib import Path

from conftest import ALPHA_BUNDLE, STAGE_PATH, TWCTL_BIN
from tw1_independent_math import golden_stage_after_load


def test_twctl_release_build_artifact():
    """Workspace must ship /app/bin/twctl."""
    assert Path(TWCTL_BIN).is_file()


def test_release_alpha_policy_present():
    """Bundled release-alpha bundle is present per fixture-catalog.md."""
    assert ALPHA_BUNDLE.is_dir()
    assert (ALPHA_BUNDLE / "policy.json").is_file()
    assert (ALPHA_BUNDLE / "witnesses").is_dir()


def test_load_materializes_tw_approval_stage(twctl, stage_reader):
    """load writes normalized staging at /app/state/tw-approval-stage.json."""
    twctl.load_bundle(ALPHA_BUNDLE)
    assert STAGE_PATH.is_file()
    staging = stage_reader(STAGE_PATH)
    assert staging["policy"]["release_id"] == "app-v2.4.0"
    assert len(staging["witnesses"]) == 4


def test_consecutive_load_bumps_ingest_seq(twctl, stage_reader):
    """Each load increments ingest_seq."""
    twctl.load_bundle(ALPHA_BUNDLE)
    first = stage_reader(STAGE_PATH)["ingest_seq"]
    twctl.load_bundle(ALPHA_BUNDLE)
    second = stage_reader(STAGE_PATH)["ingest_seq"]
    assert second == first + 1


def test_replay_merge_skips_duplicate_ids(twctl, stage_reader):
    """replay-idempotency.md deduplicates witness ids on re-load."""
    twctl.load_bundle(ALPHA_BUNDLE)
    first_seq = stage_reader(STAGE_PATH)["ingest_seq"]
    twctl.load_bundle(ALPHA_BUNDLE)
    staging = stage_reader(STAGE_PATH)
    assert staging["replay_deduped"] == 4
    assert len(staging["witnesses"]) == 4
    assert staging["ingest_seq"] == first_seq + 1


def test_staging_artifact_digest_matches_golden(twctl, stage_reader):
    """artifact_digest is sha256 of bundle artifact bytes."""
    twctl.load_bundle(ALPHA_BUNDLE)
    staging = stage_reader(STAGE_PATH)
    golden = golden_stage_after_load(ALPHA_BUNDLE, None)
    assert staging["artifact_digest"] == golden["artifact_digest"]
