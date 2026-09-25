"""Behavioral verifier for blevectl rollback and collator barriers."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from reference_bleve_index import expected_export, load_records, validate_records

APP = Path("/app")
CLI = Path("/usr/local/bin/blevectl")
FIXTURES = APP / "fixtures" / "batches"
HIDDEN = Path("/opt/verifier-fixtures/batches")
OUT = APP / "output"
STATE = APP / "state"
BATCH_SNAPSHOT = Path("/app/state/batch-snapshot.json")
INDEXES_ROOT = Path("/app/state/indexes")
TB3_INDEXES_ROOT = Path("/app/state/tb3-indexes")
COLLATOR = APP / "config" / "collator.json"
TB3_PREFIX = "/app/state/tb3-indexes"

BASELINE_RECORDS = 3
HIDDEN_RECORDS = 4
MIN_MERGE_SEGMENTS = 2
BASELINE_NEXT_DOC_ID = 4

FNV_OFFSET = 14695981039346656037
FNV_PRIME = 1099511628211
U64_MASK = 0xFFFFFFFFFFFFFFFF

PROTECTED_RELS = (
    "config/collator.json",
    "docs/batch-pipeline.md",
    "docs/export-manifest.md",
    "docs/rollback-barrier.md",
    "docs/collator-config.md",
    "docs/staging-snapshot.md",
    "docs/zap-segment-format.md",
    "src/decoy/zap_wrap.rs",
)
PROTECTED_SHA = {
    rel: hashlib.sha256((APP / rel).read_bytes()).hexdigest()
    for rel in PROTECTED_RELS
    if (APP / rel).exists()
}


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Invoke blevectl with an isolated index prefix."""
    env = os.environ.copy()
    env["TB3_INDEX_PREFIX"] = TB3_PREFIX
    return subprocess.run(
        [str(CLI), *args],
        cwd=APP,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def reset_state() -> None:
    """Restore pristine index state between tests."""
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def fnv1a_64(data: bytes) -> int:
    """Return the FNV-1a near-miss hash (xor then multiply) of data."""
    hashed = FNV_OFFSET
    for byte in data:
        hashed ^= byte
        hashed = (hashed * FNV_PRIME) & U64_MASK
    return hashed


def near_miss_unlisted_rank0(keys: list[str]) -> list[str]:
    """Return the ordering produced when unlisted keys collapse to rank 0."""
    cfg = json.loads(COLLATOR.read_text(encoding="utf-8"))
    rank = {key: index for index, key in enumerate(cfg["key_order"])}
    return sorted(keys, key=lambda key: (rank.get(key, 0), key))


def batch_keys(batch: Path) -> list[str]:
    """Return record keys in batch file order."""
    return [row["key"] for row in load_records(batch)]


@pytest.fixture(autouse=True)
def _clean_environment() -> None:
    """Reset state and output between tests."""
    reset_state()
    OUT.mkdir(parents=True, exist_ok=True)


def test_protected_environment_files_unchanged() -> None:
    """Non-target docs/config and decoy module must remain untouched."""
    for rel, sha in PROTECTED_SHA.items():
        current = hashlib.sha256((APP / rel).read_bytes()).hexdigest()
        assert current == sha, rel


def test_ingest_export_matches_reference_baseline() -> None:
    """Baseline ingest then export must match reference counts and ordering."""
    batch = FIXTURES / "baseline.jsonl"
    expected = expected_export([batch], COLLATOR)

    ingest = run_cli(["ingest", "--index", "alpha", "--batch", str(batch)])
    assert ingest.returncode == 0, ingest.stderr or ingest.stdout

    out = OUT / "baseline-manifest.json"
    export = run_cli(["export", "--index", "alpha", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout

    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["doc_count"] == expected["doc_count"]
    assert manifest["ordered_keys"] == expected["ordered_keys"]
    assert BATCH_SNAPSHOT.is_file()


def test_checksum_failure_rolls_back_state_and_counter() -> None:
    """Checksum failure must not advance doc count or leave stale pointers."""
    baseline = FIXTURES / "baseline.jsonl"
    bad_batch = FIXTURES / "checksum-fail-trap.jsonl"

    first = run_cli(["ingest", "--index", "alpha", "--batch", str(baseline)])
    assert first.returncode == 0, first.stderr or first.stdout

    root = Path(TB3_PREFIX) / "alpha"
    meta_before = json.loads((root / "meta.json").read_text(encoding="utf-8"))

    bad = run_cli(["ingest", "--index", "alpha", "--batch", str(bad_batch)])
    assert bad.returncode != 0, "checksum-fail ingest unexpectedly succeeded"

    meta_after = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    assert meta_after["next_doc_id"] == meta_before["next_doc_id"]

    root_map = json.loads((root / "root-map.json").read_text(encoding="utf-8"))
    for seg in root_map["segments"]:
        assert (root / "segments" / seg).exists(), f"stale pointer: {seg}"

    out = OUT / "after-failure.json"
    export = run_cli(["export", "--index", "alpha", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout


def test_collator_order_fixture_differs_from_bytewise_sort() -> None:
    """Bundled batch must sort by rank, not byte order or rank-0 collapse."""
    batch = FIXTURES / "collator-order.jsonl"
    expected = expected_export([batch], COLLATOR)
    keys = batch_keys(batch)
    assert expected["ordered_keys"] != sorted(keys)
    assert expected["ordered_keys"] != near_miss_unlisted_rank0(keys)

    ingest = run_cli(["ingest", "--index", "collator", "--batch", str(batch)])
    assert ingest.returncode == 0, ingest.stderr or ingest.stdout

    out = OUT / "collator-manifest.json"
    export = run_cli(["export", "--index", "collator", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["ordered_keys"] == expected["ordered_keys"]


def test_merge_not_scheduled_during_single_open_batch() -> None:
    """Single-batch ingest must not emit a merge plan for one segment."""
    batch = FIXTURES / "baseline.jsonl"
    result = run_cli(["ingest", "--index", "alpha", "--batch", str(batch)])
    assert result.returncode == 0, result.stderr or result.stdout
    merge_plan = Path(TB3_PREFIX) / "alpha" / "merge-plan.json"
    assert not merge_plan.exists()
    assert INDEXES_ROOT.is_dir()
    assert TB3_INDEXES_ROOT.is_dir()


def test_hidden_fixture_collator_order_and_staging_snapshot() -> None:
    """Hidden fixture export must obey collator order and snapshot state."""
    batch = HIDDEN / "hidden-collator.jsonl"
    expected = expected_export([batch], COLLATOR)

    ingest = run_cli(["ingest", "--index", "hidden", "--batch", str(batch)])
    assert ingest.returncode == 0, ingest.stderr or ingest.stdout

    snapshot = json.loads(BATCH_SNAPSHOT.read_text(encoding="utf-8"))
    assert snapshot["status"] == "committed"
    assert snapshot["record_count"] == HIDDEN_RECORDS

    out = OUT / "hidden-manifest.json"
    export = run_cli(["export", "--index", "hidden", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["ordered_keys"] == expected["ordered_keys"]


def test_partial_fix_on_decoy_or_export_only_is_insufficient() -> None:
    """Root-map pointers must match on-disk segments before export succeeds."""
    baseline = FIXTURES / "baseline.jsonl"
    hidden_bad = HIDDEN / "hidden-rollback.jsonl"

    ok = run_cli(["ingest", "--index", "trap", "--batch", str(baseline)])
    assert ok.returncode == 0, ok.stderr or ok.stdout

    failed = run_cli(["ingest", "--index", "trap", "--batch", str(hidden_bad)])
    assert failed.returncode != 0

    root = Path(TB3_PREFIX) / "trap"
    root_map = json.loads((root / "root-map.json").read_text(encoding="utf-8"))
    for seg in root_map["segments"]:
        assert (root / "segments" / seg).exists(), f"stale pointer: {seg}"

    out = OUT / "trap-manifest.json"
    export = run_cli(["export", "--index", "trap", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout


def test_second_ingest_writes_merge_plan_when_two_segments() -> None:
    """Merge scheduling must begin only after two committed segments exist."""
    batch = FIXTURES / "baseline.jsonl"
    root = Path(TB3_PREFIX) / "merge"
    first = run_cli(["ingest", "--index", "merge", "--batch", str(batch)])
    assert first.returncode == 0, first.stderr or first.stdout
    merge_plan = root / "merge-plan.json"
    assert not merge_plan.exists()

    second = run_cli(["ingest", "--index", "merge", "--batch", str(batch)])
    assert second.returncode == 0, second.stderr or second.stdout
    assert merge_plan.is_file()
    payload = json.loads(merge_plan.read_text(encoding="utf-8"))
    assert payload["scheduled"] is True
    assert payload["open_batch"] is False
    assert payload["segment_count"] >= MIN_MERGE_SEGMENTS
    root_map = json.loads((root / "root-map.json").read_text(encoding="utf-8"))
    assert payload["segments"] == root_map["segments"]
    assert len(payload["segments"]) >= MIN_MERGE_SEGMENTS


def test_baseline_export_doc_count_matches_reference() -> None:
    """Baseline export manifest doc_count must match the reference tally."""
    batch = FIXTURES / "baseline.jsonl"
    expected = expected_export([batch], COLLATOR)
    ingest = run_cli(["ingest", "--index", "count", "--batch", str(batch)])
    assert ingest.returncode == 0, ingest.stderr or ingest.stdout
    out = OUT / "count-manifest.json"
    export = run_cli(["export", "--index", "count", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["doc_count"] == expected["doc_count"] == BASELINE_RECORDS


def test_checksum_failure_snapshot_status_rolled_back() -> None:
    """Checksum failure must mark the staging snapshot rolled_back."""
    bad_batch = FIXTURES / "checksum-fail-trap.jsonl"
    result = run_cli(["ingest", "--index", "snap", "--batch", str(bad_batch)])
    assert result.returncode != 0
    snapshot = json.loads(BATCH_SNAPSHOT.read_text(encoding="utf-8"))
    assert snapshot["status"] == "rolled_back"


def test_checksum_trap_ingest_exit_nonzero() -> None:
    """Checksum-invalid batch lines must fail ingest with non-zero exit."""
    bad_batch = FIXTURES / "checksum-fail-trap.jsonl"
    result = run_cli(["ingest", "--index", "exit", "--batch", str(bad_batch)])
    assert result.returncode != 0, result.stdout


def test_baseline_meta_advances_doc_id_counter() -> None:
    """Successful ingest must advance next_doc_id in index meta."""
    batch = FIXTURES / "baseline.jsonl"
    root = Path(TB3_PREFIX) / "meta"
    result = run_cli(["ingest", "--index", "meta", "--batch", str(batch)])
    assert result.returncode == 0, result.stderr or result.stdout
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    assert meta["next_doc_id"] == BASELINE_NEXT_DOC_ID


def test_failed_ingest_preserves_segment_file_count() -> None:
    """Failed ingest must not add segment files beyond committed pointers."""
    baseline = FIXTURES / "baseline.jsonl"
    bad_batch = FIXTURES / "checksum-fail-trap.jsonl"
    index_root = Path(TB3_PREFIX) / "segcount"
    ok = run_cli(["ingest", "--index", "segcount", "--batch", str(baseline)])
    assert ok.returncode == 0
    seg_dir = index_root / "segments"
    before = len(list(seg_dir.glob("*.json")))
    bad = run_cli(["ingest", "--index", "segcount", "--batch", str(bad_batch)])
    assert bad.returncode != 0
    after = len(list(seg_dir.glob("*.json")))
    assert after == before


def test_export_manifest_includes_ordered_keys_list() -> None:
    """Export manifest must include an ordered_keys array."""
    batch = FIXTURES / "collator-order.jsonl"
    ingest = run_cli(["ingest", "--index", "keys", "--batch", str(batch)])
    assert ingest.returncode == 0, ingest.stderr or ingest.stdout
    out = OUT / "keys-manifest.json"
    export = run_cli(["export", "--index", "keys", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(manifest["ordered_keys"], list)
    assert len(manifest["ordered_keys"]) == manifest["doc_count"]


def test_hidden_rollback_batch_fails_ingest() -> None:
    """Hidden rollback fixture must fail ingest without stale pointers."""
    baseline = FIXTURES / "baseline.jsonl"
    hidden_bad = HIDDEN / "hidden-rollback.jsonl"
    ok = run_cli(["ingest", "--index", "hroll", "--batch", str(baseline)])
    assert ok.returncode == 0
    failed = run_cli(["ingest", "--index", "hroll", "--batch", str(hidden_bad)])
    assert failed.returncode != 0


def test_hidden_collator_export_matches_reference_keys() -> None:
    """Hidden collator fixture ordered_keys must match reference ordering."""
    batch = HIDDEN / "hidden-collator.jsonl"
    expected = expected_export([batch], COLLATOR)
    keys = batch_keys(batch)
    assert expected["ordered_keys"] != near_miss_unlisted_rank0(keys)

    ingest = run_cli(["ingest", "--index", "hkeys", "--batch", str(batch)])
    assert ingest.returncode == 0, ingest.stderr or ingest.stdout
    out = OUT / "hkeys-manifest.json"
    export = run_cli(["export", "--index", "hkeys", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["ordered_keys"] == expected["ordered_keys"]


def test_hidden_mixed_collator_rejects_rank0_collapse() -> None:
    """Mixed listed/unlisted keys must not collapse unlisted onto rank 0."""
    batch = HIDDEN / "hidden-mixed-collator.jsonl"
    expected = expected_export([batch], COLLATOR)
    keys = batch_keys(batch)
    assert expected["ordered_keys"] == ["omega", "alfa", "beta", "gamma"]
    assert expected["ordered_keys"] != near_miss_unlisted_rank0(keys)

    ingest = run_cli(["ingest", "--index", "hmix", "--batch", str(batch)])
    assert ingest.returncode == 0, ingest.stderr or ingest.stdout
    out = OUT / "hmix-manifest.json"
    export = run_cli(["export", "--index", "hmix", "--out", str(out)])
    assert export.returncode == 0, export.stderr or export.stdout
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["ordered_keys"] == expected["ordered_keys"]


def test_baseline_fixture_checksums_validate_in_reference() -> None:
    """Bundled baseline fixture must validate under FNV-1 reference rules."""
    batch = FIXTURES / "baseline.jsonl"
    rows = load_records(batch)
    assert validate_records(rows)


def test_fnv1a_near_miss_does_not_match_fixture_checksums() -> None:
    """Fixtures are FNV-1; the FNV-1a near-miss must not validate them."""
    batch = FIXTURES / "baseline.jsonl"
    for row in load_records(batch):
        record = f'{row["id"]}:{row["key"]}:{row["payload"]}'
        assert fnv1a_64(record.encode()) != int(row["checksum"])


def test_open_batch_snapshot_status_before_commit() -> None:
    """Committed ingest must leave snapshot status committed with counts."""
    batch = FIXTURES / "baseline.jsonl"
    result = run_cli(["ingest", "--index", "open", "--batch", str(batch)])
    assert result.returncode == 0, result.stderr or result.stdout
    snapshot = json.loads(BATCH_SNAPSHOT.read_text(encoding="utf-8"))
    assert snapshot["status"] == "committed"
    assert snapshot["record_count"] == BASELINE_RECORDS


def test_open_batch_flag_cleared_before_merge_plan() -> None:
    """Merge plans may exist only once open-batch.flag has been cleared."""
    batch = FIXTURES / "baseline.jsonl"
    index = "fence"
    root = Path(TB3_PREFIX) / index
    assert run_cli(["ingest", "--index", index, "--batch", str(batch)]).returncode == 0
    assert not (root / "open-batch.flag").exists()
    assert not (root / "merge-plan.json").exists()
    assert run_cli(["ingest", "--index", index, "--batch", str(batch)]).returncode == 0
    assert not (root / "open-batch.flag").exists()
    plan = root / "merge-plan.json"
    assert plan.is_file()
    payload = json.loads(plan.read_text(encoding="utf-8"))
    assert payload["open_batch"] is False
    assert "segments" in payload
