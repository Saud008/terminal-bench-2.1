"""
Verifier for redbtool page-registry staging, commit barrier, and export isolation.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from reference_btree import (
    BTree,
    apply_batch,
    leaf_count,
    load_batch,
    ordered_entries,
)

APP = Path("/app")
CLI = "/usr/local/bin/redbtool"
OUT = APP / "output"
STATE = APP / "state"
RESET = APP / "scripts/reset-state.sh"
FIXTURES = APP / "fixtures"
HIDDEN = Path("/opt/verifier-fixtures/redb-btree")
SNAPSHOT = STATE / "btree-snapshot.json"


def _run(
    cmd: list[str],
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def _reset() -> None:
    subprocess.run(["bash", str(RESET)], check=True)


def _batch(table: str, batch: Path) -> None:
    proc = _run([CLI, "batch", "--table", table, "--input", str(batch)])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def _commit(table: str) -> None:
    proc = _run([CLI, "commit", "--table", table])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def _export(table: str, out: Path) -> list[dict]:
    proc = _run([CLI, "export", "--table", table, "--out", str(out)])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def _walk(table: str) -> dict:
    proc = _run([CLI, "walk", "--table", table])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout.strip())


def test_baseline_export_matches_reference() -> None:
    """Baseline batch commit export must match independent B-tree reference."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _commit(table)
    out = OUT / "baseline.json"
    rows = _export(table, out)
    ref = BTree()
    apply_batch(ref, load_batch(str(FIXTURES / "baseline.batch.jsonl")))
    expected = ordered_entries(ref)
    assert rows == expected


def test_export_reads_committed_not_staging() -> None:
    """Export after batch without commit must not expose staging rows."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    out = OUT / "uncommitted.json"
    rows = _export(table, out)
    assert rows == []


def test_replay_batch_no_duplicate_leaf_entries() -> None:
    """Repeated put keys in one batch must not inflate physical leaf entries."""
    _reset()
    table = "replay"
    _batch(table, FIXTURES / "replay.batch.jsonl")
    _commit(table)
    report = _walk(table)
    assert report["key_count"] == 1
    assert report["physical_entry_count"] == 1
    rows = _export(table, OUT / "replay.json")
    assert rows == [{"key": "dup", "value": "third"}]


def test_delete_heavy_matches_reference() -> None:
    """Delete-heavy workload must match reference export and leaf count."""
    _reset()
    table = "delheavy"
    _batch(table, FIXTURES / "delete_heavy.batch.jsonl")
    _commit(table)
    rows = _export(table, OUT / "delete.json")
    ref = BTree()
    apply_batch(ref, load_batch(str(FIXTURES / "delete_heavy.batch.jsonl")))
    assert rows == ordered_entries(ref)
    report = _walk(table)
    assert report["leaf_count"] == leaf_count(ref)


def test_snapshot_matches_walk_after_commit() -> None:
    """btree-snapshot.json must match walk metrics after commit."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _commit(table)
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    walk = _walk(table)
    assert snap["table"] == table
    assert snap["root_height"] == walk["root_height"]
    assert snap["leaf_count"] == walk["leaf_count"]
    assert snap["key_count"] == walk["key_count"]


def test_commit_barrier_records_height_after_child_fsync() -> None:
    """Commit record must not flag height_recorded_before_child_fsync after success."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _commit(table)
    walk = _walk(table)
    assert walk["height_recorded_before_child_fsync"] is False
    record = json.loads((STATE / "commit_record.json").read_text(encoding="utf-8"))
    assert record["children_fsynced"] is True
    assert record.get("height_recorded_before_child_fsync", False) is False


def test_tb3_table_prefix_absolute() -> None:
    """TB3_TABLE_PREFIX builds absolute table namespace for batch and export."""
    _reset()
    prefix = "/app/state/tb3_lane"
    table = "lane_a"
    env = {"TB3_TABLE_PREFIX": prefix}
    batch_path = FIXTURES / "replay.batch.jsonl"
    proc = _run(
        [CLI, "batch", "--table", table, "--input", str(batch_path)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    _run([CLI, "commit", "--table", table], env=env)
    out_path = OUT / "tb3.json"
    proc = _run(
        [CLI, "export", "--table", table, "--out", str(out_path)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    rows = json.loads((OUT / "tb3.json").read_text(encoding="utf-8"))
    assert rows == [{"key": "dup", "value": "third"}]


def test_hidden_delete_fixture_matches_reference() -> None:
    """Hidden delete-heavy fixture under /opt must match reference export."""
    _reset()
    hidden_batch = HIDDEN / "tb3_delete.batch.jsonl"
    assert hidden_batch.is_file(), "hidden fixture missing"
    table = "tb3_hidden"
    _batch(table, hidden_batch)
    _commit(table)
    rows = _export(table, OUT / "hidden.json")
    ref = BTree()
    apply_batch(ref, load_batch(str(hidden_batch)))
    assert rows == ordered_entries(ref)


def test_odd_split_sequence_key_order() -> None:
    """Odd-count leaf split must preserve sorted export for five-key insert."""
    _reset()
    table = "odd5"
    batch = OUT / "odd5.batch.jsonl"
    keys = ["m01", "m02", "m03", "m04", "m05"]
    with batch.open("w", encoding="utf-8") as fh:
        for k in keys:
            fh.write(json.dumps({"op": "put", "key": k, "value": k}) + "\n")
    _batch(table, batch)
    _commit(table)
    rows = _export(table, OUT / "odd5.json")
    ref = BTree()
    apply_batch(ref, load_batch(str(batch)))
    assert rows == ordered_entries(ref)


def test_second_commit_idempotent_export() -> None:
    """Re-commit after empty staging must not change committed export."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _commit(table)
    first = _export(table, OUT / "first.json")
    _commit(table)
    second = _export(table, OUT / "second.json")
    assert first == second


def test_walk_key_count_matches_export_len() -> None:
    """Walk key_count must equal sealed export row count after commit."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _commit(table)
    rows = _export(table, OUT / "walk_keys.json")
    walk = _walk(table)
    assert walk["key_count"] == len(rows)


def test_staging_batch_does_not_write_snapshot() -> None:
    """Batch without commit must not publish btree-snapshot.json."""
    _reset()
    if SNAPSHOT.exists():
        SNAPSHOT.unlink()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    assert not SNAPSHOT.exists()


def test_delete_then_put_roundtrip() -> None:
    """Delete then put of the same key must leave the later value committed."""
    _reset()
    table = "roundtrip"
    batch = OUT / "roundtrip.batch.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({"op": "put", "key": "k1", "value": "a"}) + "\n")
        fh.write(json.dumps({"op": "delete", "key": "k1"}) + "\n")
        fh.write(json.dumps({"op": "put", "key": "k1", "value": "b"}) + "\n")
    _batch(table, batch)
    _commit(table)
    rows = _export(table, OUT / "roundtrip.json")
    assert rows == [{"key": "k1", "value": "b"}]


def test_empty_table_export_is_empty_array() -> None:
    """Export of a never-batched table must yield an empty JSON array."""
    _reset()
    rows = _export("missing", OUT / "missing.json")
    assert rows == []


def test_multi_table_isolation() -> None:
    """Committing one table must not leak keys into another table export."""
    _reset()
    _batch("alpha", FIXTURES / "replay.batch.jsonl")
    _commit("alpha")
    _batch("beta", FIXTURES / "baseline.batch.jsonl")
    _commit("beta")
    alpha = _export("alpha", OUT / "alpha.json")
    beta = _export("beta", OUT / "beta.json")
    assert alpha == [{"key": "dup", "value": "third"}]
    ref = BTree()
    apply_batch(ref, load_batch(str(FIXTURES / "baseline.batch.jsonl")))
    assert beta == ordered_entries(ref)
    assert alpha != beta


def test_seven_key_split_preserves_order() -> None:
    """Seven put keys forcing multiple splits must stay sorted in export."""
    _reset()
    table = "seven"
    batch = OUT / "seven.batch.jsonl"
    keys = [f"s{i:02d}" for i in range(1, 8)]
    with batch.open("w", encoding="utf-8") as fh:
        for k in keys:
            fh.write(json.dumps({"op": "put", "key": k, "value": k}) + "\n")
    _batch(table, batch)
    _commit(table)
    rows = _export(table, OUT / "seven.json")
    ref = BTree()
    apply_batch(ref, load_batch(str(batch)))
    assert rows == ordered_entries(ref)


def test_hidden_prefix_export_isolation() -> None:
    """Hidden fixture under TB3 prefix must not appear on the default table."""
    _reset()
    hidden_batch = HIDDEN / "tb3_delete.batch.jsonl"
    assert hidden_batch.is_file()
    prefix = "/app/state/tb3_iso"
    env = {"TB3_TABLE_PREFIX": prefix}
    table = "iso"
    proc = _run(
        [CLI, "batch", "--table", table, "--input", str(hidden_batch)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    _run([CLI, "commit", "--table", table], env=env)
    default_rows = _export("iso", OUT / "iso_default.json")
    assert default_rows == []
    proc = _run(
        [CLI, "export", "--table", table, "--out", str(OUT / "iso_pref.json")],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    pref_rows = json.loads((OUT / "iso_pref.json").read_text(encoding="utf-8"))
    ref = BTree()
    apply_batch(ref, load_batch(str(hidden_batch)))
    assert pref_rows == ordered_entries(ref)


def test_commit_clears_staging_visibility() -> None:
    """After commit, a fresh export must ignore any pre-commit staging bytes."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _commit(table)
    staging = STATE / "staging.json"
    if staging.is_file():
        data = json.loads(staging.read_text(encoding="utf-8"))
        assert table not in data or not data.get(table)
    rows = _export(table, OUT / "cleared.json")
    ref = BTree()
    apply_batch(ref, load_batch(str(FIXTURES / "baseline.batch.jsonl")))
    assert rows == ordered_entries(ref)
