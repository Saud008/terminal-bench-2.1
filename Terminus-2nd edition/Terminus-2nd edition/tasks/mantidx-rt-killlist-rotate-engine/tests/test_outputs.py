"""Behavioral checks for mantidx RT rotate / killlist / merge pipeline."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest
from reference_rt import merge_killlist_by_segment_order, reference_hits

APP = Path("/app")
STATE = APP / "state"
DB = APP / "data" / "mantidx.db"
FIXTURES = APP / "fixtures" / "docs"
HIDDEN = Path(os.environ["MANTIDX_HIDDEN_DOCS"])
BIN = Path("/usr/local/bin/mantidx")


def reset() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def run_mantidx(
    *args: str, env: dict | None = None
) -> subprocess.CompletedProcess[str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        [str(BIN), *args],
        cwd=str(APP),
        env=full_env,
        text=True,
        capture_output=True,
        check=False,
    )


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def docs_table() -> list[tuple[int, str, int, int]]:
    conn = sqlite3.connect(DB)
    try:
        rows = conn.execute(
            "SELECT doc_id, body, killed, price FROM docs ORDER BY doc_id"
        ).fetchall()
    finally:
        conn.close()
    return [(int(a), str(b), int(c), int(d)) for a, b, c, d in rows]


def expected_merged_order(pending: list[dict], rotating_segment: str) -> list[dict]:
    scoped = [e for e in pending if e["segment_id"] == rotating_segment]
    return merge_killlist_by_segment_order(scoped)


@pytest.fixture(autouse=True)
def _clean():
    reset()
    yield


def test_rotate_applies_killlist_before_disk_publish():
    batch_a = str(FIXTURES / "batch_a.jsonl")
    assert run_mantidx("insert", "--batch", batch_a).returncode == 0
    assert run_mantidx("delete", "--query", "obsolete").returncode == 0
    assert run_mantidx("rotate").returncode == 0
    audit = read_json(STATE / "rotate-audit.json")
    assert audit["disk_published_before_killlist"] is False
    assert audit["killlist_applied"] is True
    assert audit["killlist_applied_on_ram_tier"] is True
    rows = {doc_id: killed for doc_id, _body, killed, _price in docs_table()}
    assert rows[102] == 1
    assert rows[101] == 0


def test_binlog_checkpoint_commits_pending_on_rotate():
    batch_a = str(FIXTURES / "batch_a.jsonl")
    assert run_mantidx("insert", "--batch", batch_a).returncode == 0
    assert run_mantidx("rotate").returncode == 0
    cp = read_json(STATE / "binlog-checkpoint.json")
    meta = read_json(STATE / "rotate-meta.json")
    assert cp["rotate_seq"] == meta["rotate_seq"]
    assert cp["last_committed_seq"] >= 3
    conn = sqlite3.connect(DB)
    try:
        pending = conn.execute(
            "SELECT COUNT(*) FROM binlog_pending WHERE committed = 0"
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM binlog_pending").fetchone()[0]
    finally:
        conn.close()
    assert pending == 0
    assert total >= 3


def test_killlist_scoped_to_rotating_segment():
    batch_a = str(FIXTURES / "batch_a.jsonl")
    batch_b = str(FIXTURES / "batch_b.jsonl")
    assert run_mantidx("insert", "--batch", batch_a).returncode == 0
    assert run_mantidx("insert", "--batch", batch_b).returncode == 0
    assert run_mantidx("delete", "--query", "obsolete").returncode == 0
    assert run_mantidx("delete", "--query", "epsilon").returncode == 0
    meta_before = read_json(STATE / "rotate-meta.json")
    rotating_segment = meta_before["active_ram"][-1]
    kl_before = read_json(STATE / "killlist.json")
    assert len(kl_before["pending"]) >= 2
    expected_order = expected_merged_order(kl_before["pending"], rotating_segment)
    assert run_mantidx("rotate").returncode == 0
    kl_after = read_json(STATE / "killlist.json")
    remaining_ids = {e["doc_id"] for e in kl_after["pending"]}
    assert 102 in remaining_ids
    assert 202 not in remaining_ids
    merge_audit = read_json(STATE / "killlist-merge-audit.json")
    assert merge_audit["merged_order"] == expected_order
    applied_ids = {row["doc_id"] for row in merge_audit["merged_order"]}
    assert applied_ids == {202}
    assert all(row["segment_id"] == rotating_segment for row in merge_audit["merged_order"])


def test_merge_ram_unions_deleted_bitmap_and_marks_killed():
    batch_a = str(FIXTURES / "batch_a.jsonl")
    batch_b = str(FIXTURES / "batch_b.jsonl")
    assert run_mantidx("insert", "--batch", batch_a).returncode == 0
    assert run_mantidx("insert", "--batch", batch_b).returncode == 0
    assert run_mantidx("delete", "--query", "obsolete").returncode == 0
    meta = read_json(STATE / "rotate-meta.json")
    left, right = meta["active_ram"][-2], meta["active_ram"][-1]
    assert run_mantidx("merge-ram", "--left", left, "--right", right).returncode == 0
    audit = read_json(STATE / "merge-ram-audit.json")
    assert audit["deleted_respected"] is True
    rows = {doc_id: killed for doc_id, _body, killed, _price in docs_table()}
    assert rows[102] == 1


def test_update_attr_rejects_killed_docs():
    batch_a = str(FIXTURES / "batch_a.jsonl")
    assert run_mantidx("insert", "--batch", batch_a).returncode == 0
    assert run_mantidx("delete", "--query", "obsolete").returncode == 0
    assert run_mantidx("rotate").returncode == 0
    rc = run_mantidx("update-attr", "--doc-id", "102", "--price", "55")
    assert rc.returncode == 0
    audit = read_json(STATE / "attribute-audit.json")
    assert audit["rejected_killed"] is True
    rows = {doc_id: price for doc_id, _body, _killed, price in docs_table()}
    assert rows[102] == 0


def test_search_excludes_killed_docs():
    batch_a = str(FIXTURES / "batch_a.jsonl")
    assert run_mantidx("insert", "--batch", batch_a).returncode == 0
    assert run_mantidx("delete", "--query", "obsolete").returncode == 0
    assert run_mantidx("rotate").returncode == 0
    report_path = STATE / "search-report.json"
    assert (
        run_mantidx(
            "search",
            "--query",
            "widget",
            "--report",
            str(report_path),
        ).returncode
        == 0
    )
    report = read_json(report_path)
    docs = [(doc_id, body, killed) for doc_id, body, killed, _price in docs_table()]
    expected = reference_hits(docs, "widget")
    assert report["doc_ids"] == expected
    assert 102 not in report["doc_ids"]


def test_tb3_docs_dir_absolute_hidden_batch():
    assert HIDDEN.is_dir()
    env = {"TB3_DOCS_DIR": str(HIDDEN)}
    rc = run_mantidx("insert", "--batch", "rotate_kill.jsonl", env=env)
    assert rc.returncode == 0
    assert run_mantidx("delete", "--query", "obsolete").returncode == 0
    assert run_mantidx("rotate").returncode == 0
    rows = {doc_id: killed for doc_id, _body, killed, _price in docs_table()}
    assert rows[901] == 1
    assert rows[902] == 0
    audit = read_json(STATE / "rotate-audit.json")
    assert audit["disk_published_before_killlist"] is False
    assert audit["killlist_applied_on_ram_tier"] is True
