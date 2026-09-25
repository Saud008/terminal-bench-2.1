"""Milestone 2: delete gate ordering, publish-after-delete, search consistency."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from reference_index import load_jsonl, merge_parent_lineage, reference_hits

APP = Path("/app")
STATE = APP / "state"
DB = APP / "data" / "qwindex.db"
BATCH_A = APP / "fixtures" / "docs" / "batch_a.jsonl"
BATCH_B = APP / "fixtures" / "docs" / "batch_b.jsonl"
HIDDEN = Path("/opt/verifier-fixtures/qwindex/hidden/batch_delete.jsonl")
REPORT = STATE / "search-report.json"
DELETE_AUDIT = STATE / "delete-audit.json"
MANIFEST = STATE / "manifest.json"
CHECKPOINT = STATE / "checkpoint.json"
META = STATE / "split-meta.json"


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


def delete(query: str) -> None:
    proc = run(
        ["qwindex", "delete", "--query", query, "--state", str(STATE), "--db", str(DB)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def merge(left: str, right: str) -> None:
    proc = run(
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
    assert proc.returncode == 0, proc.stderr + proc.stdout


def search(query: str) -> dict:
    proc = run(
        [
            "qwindex",
            "search",
            "--query",
            query,
            "--state",
            str(STATE),
            "--db",
            str(DB),
            "--report",
            str(REPORT),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(REPORT.read_text(encoding="utf-8"))


def split_doc_count(split_id: str) -> int:
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE split_id = ?", (split_id,)
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _clean() -> None:
    reset()


class TestMilestone2:
    """Delete gate, publish ordering, and search after merge."""

    def test_delete_queues_tombstones_before_publish(self) -> None:
        """Delete alone must leave tombstones_applied false until split publish applies them."""
        index(BATCH_A)
        delete("quickwit")
        audit = json.loads(DELETE_AUDIT.read_text(encoding="utf-8"))
        assert audit["tombstones_applied"] is False
        publish()
        audit = json.loads(DELETE_AUDIT.read_text(encoding="utf-8"))
        assert audit["tombstones_applied"] is True
        assert audit["delete_gate_open"] is True

    def test_publish_manifest_doc_count_matches_live_docs_after_delete(self) -> None:
        """Manifest doc_count must match surviving documents when delete preceded publish."""
        docs = load_jsonl(BATCH_A)
        deleted_ids = set(reference_hits(docs, "quickwit"))
        index(BATCH_A)
        delete("quickwit")
        publish()
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        split_id = manifest["splits"][-1]["split_id"]
        expected = len(docs) - len(deleted_ids)
        assert manifest["splits"][-1]["doc_count"] == expected
        assert split_doc_count(split_id) == expected

    def test_delete_gate_before_docstore_gc_after_publish(self) -> None:
        """Doc store GC must run only after delete gate opens during publish apply."""
        index(BATCH_A)
        delete("quickwit")
        publish()
        audit = json.loads(DELETE_AUDIT.read_text(encoding="utf-8"))
        assert audit["delete_gate_open"] is True
        assert audit["docstore_gc_ran"] is True
        assert audit["tombstones_applied"] is True

    def test_search_hit_count_after_delete_merge_pipeline(self) -> None:
        """Bundled pipeline search for quickwit must match reference minus tombstones."""
        docs_a = load_jsonl(BATCH_A)
        docs_b = load_jsonl(BATCH_B)
        all_docs = docs_a + docs_b
        index(BATCH_A)
        publish()
        index(BATCH_B)
        publish()
        meta = json.loads(META.read_text(encoding="utf-8"))
        left, right = meta["active_splits"]
        delete("quickwit")
        merge(left, right)
        result = search("quickwit")
        tombstoned = set(reference_hits(all_docs, "quickwit"))
        expected = reference_hits(all_docs, "quickwit", exclude=tombstoned)
        assert result["doc_ids"] == expected
        assert result["hit_count"] == len(expected)

    def test_hidden_fixture_search_consistency(self) -> None:
        """Hidden batch under TB3_DOCS_DIR must produce reference-aligned search hits."""
        os.environ["TB3_DOCS_DIR"] = str(HIDDEN.parent)
        try:
            docs = load_jsonl(HIDDEN)
            index(Path("batch_delete.jsonl"))
            publish()
            delete("quickwit")
            publish()
            result = search("hidden")
            tombstoned = set(reference_hits(docs, "quickwit"))
            expected = reference_hits(docs, "hidden", exclude=tombstoned)
            assert result["doc_ids"] == expected
        finally:
            os.environ.pop("TB3_DOCS_DIR", None)

    def test_m1_checkpoint_partial_merge_regression(self) -> None:
        """Milestone 1 checkpoint rule must still hold after milestone 2 edits."""
        index(BATCH_A)
        publish()
        index(BATCH_B)
        publish()
        meta = json.loads(META.read_text(encoding="utf-8"))
        left, right = meta["active_splits"]
        cp_before = json.loads(CHECKPOINT.read_text(encoding="utf-8")) if CHECKPOINT.exists() else {
            "merge_seq": 0,
            "last_complete_merge": 0,
        }
        proc = run(
            [
                "qwindex",
                "merge",
                "--left",
                left,
                "--right",
                "00000000-0000-0000-0000-000000009999",
                "--state",
                str(STATE),
                "--db",
                str(DB),
            ]
        )
        assert proc.returncode != 0
        cp = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        assert cp["merge_seq"] == cp_before["merge_seq"] + 1
        assert cp["last_complete_merge"] == cp_before["last_complete_merge"]

    def test_m1_manifest_lineage_regression(self) -> None:
        """Manifest lineage from milestone 1 must remain correct in full pipeline."""
        index(BATCH_A)
        publish()
        index(BATCH_B)
        publish()
        meta = json.loads(META.read_text(encoding="utf-8"))
        left, right = meta["active_splits"]
        merge(left, right)
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entry = manifest["splits"][-1]
        assert entry["parent_split_id"] == merge_parent_lineage(left, right)
