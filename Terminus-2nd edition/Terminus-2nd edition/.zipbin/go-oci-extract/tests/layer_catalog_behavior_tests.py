"""Tar catalog ingest and overlay merge contract tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from fuse_runtime_helpers import (
    BUNDLED_STACK,
    INGEST_COUNTER,
    MEMBER_LEDGER,
    OVERLAY_VIEW,
    fuse_run_ok,
    load_json_doc,
    wipe_fuse_state,
)

FIXTURE_DIR = Path("/app/fixtures/oci-stacks")


@pytest.fixture(autouse=True)
def isolated_state() -> None:
    wipe_fuse_state()
    yield
    wipe_fuse_state()


def test_lfusewht_ingest_writes_stage_and_commit_ledgers() -> None:
    fuse_run_ok("ingest", str(BUNDLED_STACK))
    assert MEMBER_LEDGER.is_file() and INGEST_COUNTER.is_file()
    assert load_json_doc(MEMBER_LEDGER)["ingest_seq"] == load_json_doc(INGEST_COUNTER)["replay_seq"]


def test_lfusewht_ingest_indexes_all_three_layers() -> None:
    fuse_run_ok("ingest", str(BUNDLED_STACK))
    idx = {m["layer_index"] for m in load_json_doc(MEMBER_LEDGER)["members"]}
    assert idx == {0, 1, 2}


def test_lfusewht_ingest_classifies_whiteout_and_opaque_members() -> None:
    fuse_run_ok("ingest", str(BUNDLED_STACK))
    kinds = {m["type"] for m in load_json_doc(MEMBER_LEDGER)["members"]}
    assert "whiteout" in kinds and "opaque" in kinds


def test_lfusewht_overlay_materializes_layer_stack() -> None:
    fuse_run_ok("ingest", str(BUNDLED_STACK))
    fuse_run_ok("materialize")
    assert OVERLAY_VIEW.is_file()


def test_lfusewht_overlay_whiteout_removes_deleted_path() -> None:
    fuse_run_ok("ingest", str(BUNDLED_STACK))
    fuse_run_ok("materialize")
    paths = [e["path"] for e in load_json_doc(OVERLAY_VIEW)["entries"]]
    assert "/var/log/app.log" not in paths


def test_lfusewht_overlay_opaque_prunes_hidden_children() -> None:
    fuse_run_ok("ingest", str(BUNDLED_STACK))
    fuse_run_ok("materialize")
    paths = [e["path"] for e in load_json_doc(OVERLAY_VIEW)["entries"]]
    assert "/opt/cache/hidden.txt" not in paths
    assert "/opt/cache/fresh.txt" in paths


def test_lfusewht_overlay_uid_precedence_on_config() -> None:
    fuse_run_ok("ingest", str(BUNDLED_STACK))
    fuse_run_ok("materialize")
    row = {e["path"]: e for e in load_json_doc(OVERLAY_VIEW)["entries"]}["/etc/app/config.txt"]
    assert row["uid"] == 2000


def test_lfusewht_ingest_replay_seq_increments(tmp_path: Path) -> None:
    alt = tmp_path / "copy"
    alt.mkdir()
    for item in FIXTURE_DIR.iterdir():
        shutil.copy(item, alt / item.name)
    fuse_run_ok("ingest", str(alt / "stack.json"))
    first = load_json_doc(INGEST_COUNTER)["replay_seq"]
    fuse_run_ok("ingest", str(alt / "stack.json"))
    second = load_json_doc(INGEST_COUNTER)["replay_seq"]
    assert second == first + 1
