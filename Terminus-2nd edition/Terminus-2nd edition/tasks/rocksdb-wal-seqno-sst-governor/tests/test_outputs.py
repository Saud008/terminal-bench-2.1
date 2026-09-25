"""Behavioral tests for rocksctl WAL and compaction governor."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_governor import reference_checksum, reference_governor

ROCKSCTL = "/app/bin/rocksctl"
STAGE = Path("/app/state/rocksdb-stage.json")
COMPACT_STATE = Path("/app/state/compact-state.json")
GOVERNOR = Path("/app/output/fab-lsm-governor.json")
CHECKSUM = Path("/app/output/compaction-checksum.txt")
BUNDLED = Path("/app/data")
TB3_WAL = Path("/opt/verifier-fixtures/rocksdb-governor/tb3-wal")
TB3_SST = Path("/opt/verifier-fixtures/rocksdb-governor/tb3-sst")


def _run(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def _fresh() -> None:
    for p in (STAGE, COMPACT_STATE, GOVERNOR, CHECKSUM):
        if p.exists():
            p.unlink()


def _ingest(fixture_dir: Path) -> None:
    _run([ROCKSCTL, "wal", "ingest", str(fixture_dir)])


def _export(pass_n: int = 1) -> None:
    if pass_n == 1:
        _run([ROCKSCTL, "compact", "plan", "export"])
    else:
        _run([ROCKSCTL, "compact", "plan", "export", "--pass", str(pass_n)])


def _pipeline(fixture_dir: Path, pass_n: int = 1) -> None:
    _fresh()
    _ingest(fixture_dir)
    _export(pass_n)


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_rocksctl_binary_exists():
    """Instruction requires /app/bin/rocksctl built from workspace."""
    assert Path(ROCKSCTL).is_file()


def test_bundled_fixture_layout_exists():
    """Instruction cites bundled fixtures under /app/data/."""
    assert (BUNDLED / "manifest.json").is_file()
    assert (BUNDLED / "wal" / "01_committed.json").is_file()
    assert (BUNDLED / "sst" / "01_alpha.json").is_file()


def test_wal_ingest_writes_staging_snapshot():
    """Ingest must write normalized staging at /app/state/rocksdb-stage.json."""
    _ingest(BUNDLED)
    assert STAGE.is_file()
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    assert len(data["wal_batches"]) == 2
    assert len(data["sst_files"]) == 3


def test_staging_preserves_wal_source_order():
    """Staging lists wal batches in source filename order per instruction."""
    _ingest(BUNDLED)
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    sources = [b["source"] for b in data["wal_batches"]]
    assert sources == ["01_committed.json", "02_uncommitted.json"]


def test_staging_snapshot_seqno_from_manifest():
    """Staging copies snapshot_seqno and watermark_seqno from manifest."""
    _ingest(BUNDLED)
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    assert data["snapshot_seqno"] == 125
    assert data["watermark_seqno"] == 120


def test_ingest_seq_monotonic():
    """Ingest increments ingest_seq on each ingest call."""
    _ingest(BUNDLED)
    first = json.loads(STAGE.read_text(encoding="utf-8"))["ingest_seq"]
    _ingest(BUNDLED)
    second = json.loads(STAGE.read_text(encoding="utf-8"))["ingest_seq"]
    assert second == first + 1


def test_compact_export_creates_artifacts():
    """compact plan export writes governor JSON and checksum under /app/output/."""
    _pipeline(BUNDLED)
    assert GOVERNOR.is_file()
    assert CHECKSUM.is_file()


def test_selected_sst_respects_watermark():
    """compaction-watermark-planner.md excludes SST above watermark_seqno."""
    _pipeline(BUNDLED)
    got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
    ref = reference_governor(STAGE)
    assert got["selected_sst"] == ref["selected_sst"] == ["L0_alpha", "L0_beta"]


def test_uncommitted_wal_not_visible():
    """seqno-visibility.md excludes uncommitted batches below snapshot."""
    _pipeline(BUNDLED)
    got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
    ref = reference_governor(STAGE)
    default_keys = {row["key"] for row in got["visible_keys"].get("default", [])}
    assert "trace/shadow" not in default_keys
    ref_keys = {row["key"] for row in ref["visible_keys"].get("default", [])}
    assert "trace/shadow" not in ref_keys


def test_wal_put_wins_over_older_sst():
    """Latest seqno per key: committed WAL put beats older SST value."""
    _pipeline(BUNDLED)
    got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
    trace1 = next(r for r in got["visible_keys"]["default"] if r["key"] == "trace/1")
    assert trace1["value"] == "wal_v"
    assert trace1["seqno"] == 100


def test_range_tombstone_exclusive_end():
    """range-tombstone-bounds.md keeps range/p visible while hiding range/m..range/o."""
    _pipeline(BUNDLED)
    got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
    keys = {r["key"] for r in got["visible_keys"]["default"]}
    assert "range/m" not in keys
    assert "range/n" not in keys
    assert "range/o" not in keys
    assert "range/p" in keys


def test_merge_operator_finalized_sum():
    """merge-operator-finalize.md sums operands instead of publishing partial_value."""
    _pipeline(BUNDLED)
    got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
    rollup = next(r for r in got["visible_keys"]["default"] if r["key"] == "rollup/total")
    assert rollup["value"] == "30"


def test_reclaimed_bytes_sum_selected_sst():
    """reclaim-idempotency.md sums size_bytes of watermark-eligible SST only."""
    _pipeline(BUNDLED)
    got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
    ref = reference_governor(STAGE)
    assert got["reclaimed_bytes"] == ref["reclaimed_bytes"] == 10240


def test_checksum_matches_reference():
    """export-checksum.md digest must match independent reference."""
    _pipeline(BUNDLED)
    digest = CHECKSUM.read_text(encoding="utf-8").strip()
    assert digest == reference_checksum(STAGE)
    assert len(digest) == 64


def test_second_compact_pass_idempotent_reclaim():
    """reclaim-idempotency.md pass 2 must match pass 1 reclaimed_bytes."""
    _pipeline(BUNDLED)
    first = json.loads(GOVERNOR.read_text(encoding="utf-8"))["reclaimed_bytes"]
    first_digest = CHECKSUM.read_text(encoding="utf-8").strip()
    _export(2)
    second = json.loads(GOVERNOR.read_text(encoding="utf-8"))["reclaimed_bytes"]
    second_digest = CHECKSUM.read_text(encoding="utf-8").strip()
    assert second == first == 10240
    assert second_digest == first_digest


def test_output_paths_contract():
    """Instruction output paths are honored."""
    _pipeline(BUNDLED)
    assert str(GOVERNOR) == "/app/output/fab-lsm-governor.json"
    assert str(CHECKSUM) == "/app/output/compaction-checksum.txt"


def test_staging_path_contract():
    """Instruction staging path /app/state/rocksdb-stage.json is honored."""
    _ingest(BUNDLED)
    assert STAGE == Path("/app/state/rocksdb-stage.json")


def test_compact_state_persisted():
    """Pass 1 writes compact state for reclaim idempotency tracking."""
    _pipeline(BUNDLED)
    assert COMPACT_STATE.is_file()
    state = json.loads(COMPACT_STATE.read_text(encoding="utf-8"))
    assert "reclaimed_bytes" in state


def test_reference_subprocess_cli_roundtrip():
    """Independent reference agrees after subprocess ingest and export."""
    _pipeline(BUNDLED)
    got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
    ref = reference_governor(STAGE)
    assert got["visible_keys"] == ref["visible_keys"]
    assert got["selected_sst"] == ref["selected_sst"]


def _tb3_fixture_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-rocksdb-"))
    shutil.copytree(BUNDLED / "wal", tmp / "wal")
    shutil.copytree(BUNDLED / "sst", tmp / "sst")
    shutil.copy(BUNDLED / "manifest.json", tmp / "manifest.json")
    shutil.copy(TB3_WAL / "03_tb3.json", tmp / "wal" / "03_tb3.json")
    shutil.copy(TB3_SST / "04_delta.json", tmp / "sst" / "04_delta.json")
    return tmp


def test_tb3_extra_wal_and_sst_hidden_merge():
    """Hidden WAL and SST fixtures must match reference governor output."""
    fixture = _tb3_fixture_dir()
    try:
        _pipeline(fixture)
        got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
        ref = reference_governor(STAGE)
        assert got["visible_keys"] == ref["visible_keys"]
        assert got["reclaimed_bytes"] == ref["reclaimed_bytes"]
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_tb3_key_prefix_mutation():
    """TB3_KEY_PREFIX prepends keys before visibility and tombstone checks."""
    fixture = _tb3_fixture_dir()
    try:
        _fresh()
        _ingest(fixture)
        _run(
            [ROCKSCTL, "compact", "plan", "export"],
            env={"TB3_KEY_PREFIX": "tb3/"},
        )
        got = json.loads(GOVERNOR.read_text(encoding="utf-8"))
        ref = reference_governor(STAGE, key_prefix="tb3/")
        assert got["visible_keys"] == ref["visible_keys"]
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_tb3_hidden_checksum_with_prefix():
    """Hidden fixture checksum matches reference under TB3_KEY_PREFIX."""
    fixture = _tb3_fixture_dir()
    try:
        _fresh()
        _ingest(fixture)
        _run(
            [ROCKSCTL, "compact", "plan", "export"],
            env={"TB3_KEY_PREFIX": "tb3/"},
        )
        digest = CHECKSUM.read_text(encoding="utf-8").strip()
        assert digest == reference_checksum(STAGE, key_prefix="tb3/")
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_tb3_idempotent_second_pass_hidden():
    """Hidden three-file SST catalog stays idempotent on pass 2."""
    fixture = _tb3_fixture_dir()
    try:
        _pipeline(fixture)
        first = CHECKSUM.read_text(encoding="utf-8").strip()
        _export(2)
        second = CHECKSUM.read_text(encoding="utf-8").strip()
        assert second == first
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
