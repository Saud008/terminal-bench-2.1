"""Milestone 1: merge metadata, manifest lineage, checkpoint on partial failure."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from reference_index import merge_parent_lineage

APP = Path("/app")
STATE = APP / "state"
DB = APP / "data" / "qwindex.db"
BATCH_A = APP / "fixtures" / "docs" / "batch_a.jsonl"
BATCH_B = APP / "fixtures" / "docs" / "batch_b.jsonl"
MANIFEST = STATE / "manifest.json"
CHECKPOINT = STATE / "checkpoint.json"
META = STATE / "split-meta.json"
MERGE_AUDIT = STATE / "merge-audit.json"


def reset() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def index(path: Path) -> None:
    proc = run(["qwindex", "index", "--batch", str(path), "--state", str(STATE), "--db", str(DB)])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def publish() -> None:
    proc = run(["qwindex", "split-publish", "--state", str(STATE), "--db", str(DB)])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def merge(left: str, right: str) -> subprocess.CompletedProcess[str]:
    return run(
        [
            "qwindex",
            "merge",
            "--left",
            left,
            "--right",
            right,
            "--state",
            str(STATE),
            "--db",
            str(DB),
        ]
    )


def two_splits() -> tuple[str, str]:
    index(BATCH_A)
    publish()
    index(BATCH_B)
    publish()
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert len(meta["active_splits"]) == 2
    return meta["active_splits"][0], meta["active_splits"][1]


@pytest.fixture(autouse=True)
def _clean() -> None:
    reset()


class TestMilestone1:
    """Merge cache flush, manifest lineage, checkpoint partial failure."""

    def test_partial_merge_does_not_advance_complete_checkpoint(self) -> None:
        """Unknown split merge must bump merge_seq but not last_complete_merge."""
        left, right = two_splits()
        cp_before = json.loads(CHECKPOINT.read_text(encoding="utf-8")) if CHECKPOINT.exists() else {
            "merge_seq": 0,
            "last_complete_merge": 0,
        }
        proc = merge(left, "00000000-0000-0000-0000-000000009999")
        assert proc.returncode != 0
        cp = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        assert cp["merge_seq"] == cp_before["merge_seq"] + 1
        assert cp["last_complete_merge"] == cp_before["last_complete_merge"]

    def test_merge_manifest_parent_is_lex_larger_source(self) -> None:
        """Merged manifest row parent_split_id must be the lexicographically larger source UUID."""
        left, right = two_splits()
        assert merge(left, right).returncode == 0
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entry = manifest["splits"][-1]
        expected_parent = merge_parent_lineage(left, right)
        assert entry["parent_split_id"] == expected_parent
        assert entry["parent_split_id"] != entry["split_id"]

    def test_merge_audit_cache_flushed_and_single_active_split(self) -> None:
        """Merge must flush hot cache and leave one active split in split-meta.json."""
        left, right = two_splits()
        assert merge(left, right).returncode == 0
        audit = json.loads(MERGE_AUDIT.read_text(encoding="utf-8"))
        assert audit["cache_flushed"] is True
        assert audit["status"] == "complete"
        meta = json.loads(META.read_text(encoding="utf-8"))
        assert len(meta["active_splits"]) == 1
        assert meta["active_splits"][0] == audit["merged_into"]
        assert audit["merged_into"] == min(left, right)

    def test_successful_merge_advances_complete_checkpoint(self) -> None:
        """Successful merge must increment both merge_seq and last_complete_merge."""
        left, right = two_splits()
        assert merge(left, right).returncode == 0
        cp = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        assert cp["merge_seq"] >= 1
        assert cp["last_complete_merge"] == cp["merge_seq"]

    def test_tb3_docs_dir_index_acceptance(self) -> None:
        """TB3_DOCS_DIR must resolve batch paths like bundled fixtures."""
        import os

        os.environ["TB3_DOCS_DIR"] = str(APP / "fixtures" / "docs")
        try:
            index(Path("batch_a.jsonl"))
            publish()
            meta = json.loads(META.read_text(encoding="utf-8"))
            assert len(meta["active_splits"]) == 1
        finally:
            os.environ.pop("TB3_DOCS_DIR", None)
