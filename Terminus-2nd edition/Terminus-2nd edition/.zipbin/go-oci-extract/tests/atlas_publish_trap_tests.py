"""Filesystem manifest publish and hidden overlay trap tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from fuse_runtime_helpers import (
    ATLAS_OUT,
    BUNDLED_STACK,
    INGEST_COUNTER,
    HIDDEN_STACK_ROOT,
    OVERLAY_VIEW,
    fuse_publish_all,
    fuse_run,
    fuse_run_ok,
    load_json_doc,
    wipe_fuse_state,
)
from overlay_digest_math import digest_from_stack, sorted_paths_from_stack


@pytest.fixture(autouse=True)
def isolated_state() -> None:
    wipe_fuse_state()
    yield
    wipe_fuse_state()


def test_lfusewht_publish_writes_atlas_artifact() -> None:
    fuse_publish_all(BUNDLED_STACK)
    assert ATLAS_OUT.is_file()


def test_lfusewht_publish_replay_seq_matches_commit_ledger() -> None:
    fuse_publish_all(BUNDLED_STACK)
    out = load_json_doc(ATLAS_OUT)
    commit = load_json_doc(INGEST_COUNTER)
    assert out["replay_seq"] == commit["replay_seq"]


def test_lfusewht_publish_hash_matches_canonical_digest() -> None:
    fuse_publish_all(BUNDLED_STACK)
    out = load_json_doc(ATLAS_OUT)
    ref = digest_from_stack(BUNDLED_STACK, replay_seq=out["replay_seq"])
    assert out["manifest_hash"] == ref["manifest_hash"]


def test_lfusewht_publish_entries_match_canonical_listing() -> None:
    fuse_publish_all(BUNDLED_STACK)
    out = load_json_doc(ATLAS_OUT)
    assert [r["path"] for r in out["entries"]] == sorted_paths_from_stack(BUNDLED_STACK)


def test_lfusewht_publish_requires_merged_stack_doc() -> None:
    fuse_run_ok("ingest", str(BUNDLED_STACK))
    proc = fuse_run("manifest", "export")
    assert proc.returncode != 0


def test_lfusewht_tb3_fixture_slash_entry_uid(tmp_path: Path) -> None:
    work = tmp_path / "h1"
    work.mkdir()
    for name in ("tb3-layer0.tar", "tb3-layer1.tar", "tb3-stack.json"):
        shutil.copy(HIDDEN_STACK_ROOT / name, work / name)
    fuse_publish_all(work / "tb3-stack.json")
    rows = {e["path"]: e for e in load_json_doc(OVERLAY_VIEW)["entries"]}
    assert rows["/etc/slash/app/main.txt"]["uid"] == 88


def test_lfusewht_tb3_fixture_whiteout_drops_keep_file(tmp_path: Path) -> None:
    work = tmp_path / "h2"
    work.mkdir()
    for name in ("tb3-layer0.tar", "tb3-layer1.tar", "tb3-stack.json"):
        shutil.copy(HIDDEN_STACK_ROOT / name, work / name)
    fuse_publish_all(work / "tb3-stack.json")
    entries = [e["path"] for e in load_json_doc(OVERLAY_VIEW)["entries"]]
    assert "/var/run/keep.txt" not in entries


def test_lfusewht_offpath_skirt_not_required_for_publish() -> None:
    assert Path("/app/internal/offpath/wrap.go").is_file()
    fuse_publish_all(BUNDLED_STACK)
