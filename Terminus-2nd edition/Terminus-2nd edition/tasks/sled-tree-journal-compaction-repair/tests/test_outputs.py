"""
Verifier for sledtool staging, snapshot pins, compaction, journal replay, and scan-range.
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
    range_entries,
)

APP = Path("/app")
CLI = "/usr/local/bin/sledtool"
OUT = APP / "output"
STATE = APP / "state"
COMMITTED_JSON = "/app/state/committed.json"
PAGE_REGISTRY_JSON = "/app/state/page_registry.json"
STAGING_JSON = "/app/state/staging.json"
SNAPSHOT_JSON = "/app/state/sled-staging-snapshot.json"
SPLIT_JOURNAL_JSONL = "/app/state/split_journal.jsonl"
PINS_DIR = "/app/state/pins/"
RANGE_OUTPUT_JSON = "/app/output/range.json"
RESET = APP / "scripts/reset-state.sh"
FIXTURES = APP / "fixtures"
HIDDEN = Path("/opt/verifier-fixtures/sled-journal")
SNAPSHOT = STATE / "sled-staging-snapshot.json"
REGISTRY = STATE / "page_registry.json"
JOURNAL = STATE / "split_journal.jsonl"


def reference_page_checksum(generation: int, body: bytes) -> int:
    acc = 0xFFFFFFFF
    for b in generation.to_bytes(8, "little"):
        acc = (acc * 16777619) ^ b
        acc &= 0xFFFFFFFF
    for b in body:
        acc = (acc * 16777619) ^ b
        acc &= 0xFFFFFFFF
    return acc


def _run(
    cmd: list[str], env: dict[str, str] | None = None
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


def _publish(table: str) -> None:
    proc = _run([CLI, "publish", "--table", table])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def _scan_range(table: str, start: str, end: str, out: Path) -> list[dict]:
    proc = _run(
        [
            CLI,
            "scan-range",
            "--table",
            table,
            "--start",
            start,
            "--end",
            end,
            "--out",
            str(out),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def _export(table: str, out: Path) -> list[dict]:
    proc = _run([CLI, "export", "--table", table, "--out", str(out)])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def _walk(table: str) -> dict:
    proc = _run([CLI, "walk", "--table", table])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout.strip())


def test_baseline_export_matches_reference() -> None:
    """Baseline batch publish export must match independent B-tree reference."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    assert Path(COMMITTED_JSON).is_file()
    assert Path(PAGE_REGISTRY_JSON).is_file()
    rows = _export(table, OUT / "baseline.json")
    ref = BTree()
    apply_batch(ref, load_batch(str(FIXTURES / "baseline.batch.jsonl")))
    assert rows == ordered_entries(ref)


def test_export_reads_committed_not_staging() -> None:
    """Export after batch without publish must not expose staging rows."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    rows = _export(table, OUT / "uncommitted.json")
    assert Path(STAGING_JSON).is_file()
    assert rows == []


def test_replay_batch_no_duplicate_leaf_entries() -> None:
    """Repeated put keys in one batch must not inflate physical leaf entries."""
    _reset()
    table = "replay"
    _batch(table, FIXTURES / "replay.batch.jsonl")
    _publish(table)
    report = _walk(table)
    assert report["key_count"] == 1
    assert report["physical_entry_count"] == 1


def test_delete_heavy_matches_reference() -> None:
    """Delete-heavy workload must match reference export and leaf count."""
    _reset()
    table = "delheavy"
    _batch(table, FIXTURES / "delete_heavy.batch.jsonl")
    _publish(table)
    rows = _export(table, OUT / "delete.json")
    ref = BTree()
    apply_batch(ref, load_batch(str(FIXTURES / "delete_heavy.batch.jsonl")))
    assert rows == ordered_entries(ref)
    report = _walk(table)
    assert report["leaf_count"] == leaf_count(ref)


def test_snapshot_matches_walk_after_publish() -> None:
    """sled-staging-snapshot.json must match walk metrics after publish."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    snap = json.loads(Path(SNAPSHOT_JSON).read_text(encoding="utf-8"))
    walk = _walk(table)
    assert snap["table"] == table
    assert snap["root_height"] == walk["root_height"]
    assert snap["leaf_count"] == walk["leaf_count"]
    assert snap["key_count"] == walk["key_count"]


def test_split_journal_parent_pivot_before_right_page() -> None:
    """Split journal must record parent pivot before persisting right child page."""
    _reset()
    table = "splitorder"
    batch = OUT / "splitorder.batch.jsonl"
    keys = [f"s{i:02d}" for i in range(1, 8)]
    with batch.open("w", encoding="utf-8") as fh:
        for k in keys:
            fh.write(json.dumps({"op": "put", "key": k, "value": k}) + "\n")
    _batch(table, batch)
    _publish(table)
    assert Path(SPLIT_JOURNAL_JSONL).is_file()
    by_seq: dict[int, list[str]] = {}
    for line in Path(SPLIT_JOURNAL_JSONL).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        seq = int(entry["split_seq"])
        by_seq.setdefault(seq, []).append(entry["kind"])
    for kinds in by_seq.values():
        assert kinds.index("ParentPivot") < kinds.index("RightPage")


def test_page_registry_checksum_includes_generation() -> None:
    """Page registry checksum must cover header generation counter and body."""
    _reset()
    table = "checksums"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    reg = json.loads(Path(PAGE_REGISTRY_JSON).read_text(encoding="utf-8"))
    assert reg["pages"], "page registry empty"
    for rec in reg["pages"].values():
        gen = int(rec["header"]["generation"])
        body = rec["body"].encode("utf-8")
        expected = reference_page_checksum(gen, body)
        assert rec["checksum"] == expected


def test_compaction_honors_snapshot_pins() -> None:
    """Compaction must not reclaim pages listed in snapshot pin sets."""
    _reset()
    table = "compactpin"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stale_id = "stale-pin-page"
    reg["pages"][stale_id] = {
        "header": {"page_id": stale_id, "generation": 1, "high_key": None},
        "body": "stale-body",
        "checksum": 1,
    }
    REGISTRY.write_text(json.dumps(reg), encoding="utf-8")
    pin_dir = Path(PINS_DIR)
    pin_dir.mkdir(parents=True, exist_ok=True)
    pin_file = pin_dir / f"{table}-snap-a.json"
    pin_file.write_text(
        json.dumps(
            {
                "table": table,
                "snapshot_id": "snap-a",
                "pinned_pages": [stale_id],
            }
        ),
        encoding="utf-8",
    )
    proc = _run([CLI, "compact", "--table", table])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    reg_after = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert stale_id in reg_after["pages"]


def test_journal_replay_idempotent_on_split_seq() -> None:
    """Crash journal replay twice must leave committed export unchanged."""
    _reset()
    table = "journal"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    proc = _run(
        [
            CLI,
            "journal-replay",
            "--table",
            table,
            "--journal",
            str(FIXTURES / "crash-split.journal.jsonl"),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    first = _export(table, OUT / "replay_once.json")
    proc2 = _run(
        [
            CLI,
            "journal-replay",
            "--table",
            table,
            "--journal",
            str(FIXTURES / "crash-split.journal.jsonl"),
        ]
    )
    assert proc2.returncode == 0, proc2.stderr + proc.stdout
    second = _export(table, OUT / "replay_twice.json")
    assert first == second


def test_scan_range_matches_reference_after_merge() -> None:
    """Inclusive scan-range must match reference after merge-heavy deletes."""
    _reset()
    table = "range"
    hidden_batch = HIDDEN / "tb3_merge_range.batch.jsonl"
    assert hidden_batch.is_file(), "hidden fixture missing"
    _batch(table, hidden_batch)
    _publish(table)
    rows = _scan_range(table, "h03", "h09", Path(RANGE_OUTPUT_JSON))
    ref = BTree()
    apply_batch(ref, load_batch(str(hidden_batch)))
    expected = [{"key": k, "value": v} for k, v in range_entries(ref, "h03", "h09")]
    assert rows == expected


def test_tb3_table_prefix_absolute() -> None:
    """TB3_TABLE_PREFIX builds absolute table namespace for batch and scan-range."""
    _reset()
    prefix = "/app/state/tb3_lane"
    table = "lane_a"
    env = {"TB3_TABLE_PREFIX": prefix}
    proc = _run(
        [
            CLI,
            "batch",
            "--table",
            table,
            "--input",
            str(FIXTURES / "replay.batch.jsonl"),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    _run([CLI, "publish", "--table", table], env=env)
    proc = _run(
        [
            CLI,
            "scan-range",
            "--table",
            table,
            "--start",
            "dup",
            "--end",
            "dup",
            "--out",
            str(OUT / "tb3.json"),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    rows = json.loads((OUT / "tb3.json").read_text(encoding="utf-8"))
    assert rows == [{"key": "dup", "value": "third"}]


def test_second_publish_idempotent_export() -> None:
    """Re-publish after empty staging must not change committed export."""
    _reset()
    table = "inventory"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    first = _export(table, OUT / "first.json")
    _publish(table)
    second = _export(table, OUT / "second.json")
    assert first == second


def test_delete_heavy_scan_range_matches_filtered_export() -> None:
    """Inclusive scan-range on delete-heavy table must match filtered export rows."""
    _reset()
    table = "delrange"
    _batch(table, FIXTURES / "delete_heavy.batch.jsonl")
    _publish(table)
    rows = _scan_range(table, "k03", "k09", OUT / "delrange.json")
    exported = _export(table, OUT / "delrange_export.json")
    expected = [row for row in exported if "k03" <= row["key"] <= "k09"]
    assert rows == expected


def test_walk_key_count_matches_export_length() -> None:
    """Walk key_count must equal committed export row count after publish."""
    _reset()
    table = "walkcount"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    walk = _walk(table)
    exported = _export(table, OUT / "walkcount.json")
    assert walk["key_count"] == len(exported)


def test_reference_page_checksum_fnv1_empty_body() -> None:
    """FNV-1 page checksum uses 0xFFFFFFFF basis and generation little-endian bytes."""
    assert reference_page_checksum(1, b"a") == 0x8155DF8D


def test_scan_range_empty_outside_bounds() -> None:
    """Scan-range outside committed keys returns an empty JSON list."""
    _reset()
    table = "emptyrange"
    _batch(table, FIXTURES / "replay.batch.jsonl")
    _publish(table)
    rows = _scan_range(table, "zzz", "zzz9", OUT / "emptyrange.json")
    assert rows == []


def test_snapshot_pin_creates_pin_file() -> None:
    """snapshot-pin must write a pin record under /app/state/pins/."""
    _reset()
    table = "pinfile"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    proc = _run([CLI, "snapshot-pin", "--table", table, "--snapshot-id", "snap-b"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    pin_path = Path(PINS_DIR) / f"{table}-snap-b.json"
    assert pin_path.is_file()
    payload = json.loads(pin_path.read_text(encoding="utf-8"))
    assert payload["snapshot_id"] == "snap-b"
    assert payload["table"] == table


def test_export_rows_sorted_lexicographic() -> None:
    """Export returns rows sorted by key ascending."""
    _reset()
    table = "sorted"
    _batch(table, FIXTURES / "baseline.batch.jsonl")
    _publish(table)
    rows = _export(table, OUT / "sorted.json")
    keys = [row["key"] for row in rows]
    assert keys == sorted(keys)
