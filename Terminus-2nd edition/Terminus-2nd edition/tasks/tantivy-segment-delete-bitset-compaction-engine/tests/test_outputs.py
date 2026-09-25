"""Behavioral tests for tantictl segment compaction governor."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_merge import reference_checksum, reference_stats

TANTICTL = "/app/bin/tantictl"
STAGE = Path("/app/state/tantivy-stage.json")
MERGE_STATE = Path("/app/state/merge-state.json")
STATS = Path("/app/output/segment-stats.json")
CHECKSUM = Path("/app/output/merge-checksum.txt")
BUNDLED = Path("/app/data/segments")
TB3_SRC = Path("/opt/verifier-fixtures/tantivy-segments")


def _run(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def _fresh() -> None:
    for p in (STAGE, MERGE_STATE, STATS, CHECKSUM):
        if p.exists():
            p.unlink()


def _ingest(seg_dir: Path) -> None:
    _run([TANTICTL, "ingest", str(seg_dir)])


def _export(pass_n: int = 1) -> None:
    if pass_n == 1:
        _run([TANTICTL, "merge", "export"])
    else:
        _run([TANTICTL, "merge", "export", "--pass", str(pass_n)])


def _pipeline(seg_dir: Path, pass_n: int = 1) -> None:
    _fresh()
    _ingest(seg_dir)
    _export(pass_n)


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_tantictl_binary_exists():
    """Instruction requires /app/bin/tantictl built from workspace."""
    assert Path(TANTICTL).is_file()


def test_bundled_segments_directory_exists():
    """Instruction cites bundled fixtures under /app/data/segments/."""
    assert BUNDLED.is_dir()
    assert (BUNDLED / "01_alpha.json").is_file()
    assert (BUNDLED / "02_beta.json").is_file()


def test_ingest_writes_staging_snapshot():
    """Ingest must write normalized staging at /app/state/tantivy-stage.json."""
    _ingest(BUNDLED)
    assert STAGE.is_file()
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    assert len(data["segments"]) == 2


def test_staging_preserves_source_order():
    """Staging lists segments in source filename order per instruction."""
    _ingest(BUNDLED)
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    sources = [s["source"] for s in data["segments"]]
    assert sources == ["01_alpha.json", "02_beta.json"]


def test_staging_segment_ids_preserved():
    """Staging copies segment_id values from JSON fixtures."""
    _ingest(BUNDLED)
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    ids = [s["segment_id"] for s in data["segments"]]
    assert ids == ["alpha", "beta"]


def test_ingest_seq_monotonic():
    """Ingest increments ingest_seq on each ingest call."""
    _ingest(BUNDLED)
    first = json.loads(STAGE.read_text(encoding="utf-8"))["ingest_seq"]
    _ingest(BUNDLED)
    second = json.loads(STAGE.read_text(encoding="utf-8"))["ingest_seq"]
    assert second == first + 1


def test_merge_export_creates_artifacts():
    """merge export writes stats and checksum under /app/output/."""
    _pipeline(BUNDLED)
    assert STATS.is_file()
    assert CHECKSUM.is_file()


def test_live_max_doc_union_two_segments():
    """live-max-doc-union.md requires sum of segment max_doc values."""
    _pipeline(BUNDLED)
    got = json.loads(STATS.read_text(encoding="utf-8"))
    ref = reference_stats(STAGE)
    assert got["live_max_doc"] == ref["live_max_doc"] == 7


def test_delete_bits_remapped_globally():
    """delete-bitset-remap.md requires global tombstone ids after offset."""
    _pipeline(BUNDLED)
    got = json.loads(STATS.read_text(encoding="utf-8"))
    ref = reference_stats(STAGE)
    assert got["delete_bits"] == ref["delete_bits"] == [1, 2, 5]


def test_term_freq_search_after_deletes():
    """term-freq-after-deletes.md subtracts deleted_hits before summing."""
    _pipeline(BUNDLED)
    got = json.loads(STATS.read_text(encoding="utf-8"))
    ref = reference_stats(STAGE)
    search = next(t for t in got["terms"] if t["term"] == "search")
    ref_search = next(t for t in ref["terms"] if t["term"] == "search")
    assert search["freq"] == ref_search["freq"] == 3


def test_term_freq_body_index_merge():
    """Body index term rollup matches reference across segments."""
    _pipeline(BUNDLED)
    got = json.loads(STATS.read_text(encoding="utf-8"))
    ref = reference_stats(STAGE)
    body = next(t for t in got["terms"] if t["field"] == "body" and t["term"] == "index")
    ref_body = next(t for t in ref["terms"] if t["field"] == "body" and t["term"] == "index")
    assert body["freq"] == ref_body["freq"] == 2


def test_norm_values_u8_json_width():
    """field-norm-encoding.md requires norms export as u8-width JSON numbers."""
    _pipeline(BUNDLED)
    data = json.loads(STATS.read_text(encoding="utf-8"))
    for term in data["terms"]:
        norm = term["norm"]
        assert isinstance(norm, int)
        assert 0 <= norm <= 255


def test_checksum_matches_reference():
    """export-checksum.md digest must match independent reference."""
    _pipeline(BUNDLED)
    digest = CHECKSUM.read_text(encoding="utf-8").strip()
    assert digest == reference_checksum(STAGE)
    assert len(digest) == 64


def test_second_merge_pass_idempotent():
    """merge-idempotency.md pass 2 must match pass 1 checksum."""
    _pipeline(BUNDLED)
    first_digest = CHECKSUM.read_text(encoding="utf-8").strip()
    first_bits = json.loads(STATS.read_text(encoding="utf-8"))["delete_bits"]
    _export(2)
    second_digest = CHECKSUM.read_text(encoding="utf-8").strip()
    second_bits = json.loads(STATS.read_text(encoding="utf-8"))["delete_bits"]
    assert second_digest == first_digest
    assert second_bits == first_bits


def test_output_paths_contract():
    """Instruction output paths are honored."""
    _pipeline(BUNDLED)
    assert str(STATS) == "/app/output/segment-stats.json"
    assert str(CHECKSUM) == "/app/output/merge-checksum.txt"


def test_staging_path_contract():
    """Instruction staging path /app/state/tantivy-stage.json is honored."""
    _ingest(BUNDLED)
    assert STAGE == Path("/app/state/tantivy-stage.json")


def test_merge_state_persisted():
    """Pass 1 writes merge state for idempotency tracking."""
    _pipeline(BUNDLED)
    assert MERGE_STATE.is_file()
    state = json.loads(MERGE_STATE.read_text(encoding="utf-8"))
    assert "delete_bits" in state


def test_reference_subprocess_cli_roundtrip():
    """Independent reference agrees after subprocess ingest and export."""
    _pipeline(BUNDLED)
    got = json.loads(STATS.read_text(encoding="utf-8"))
    ref = reference_stats(STAGE)
    assert got["terms"] == ref["terms"]


def _tb3_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-seg-"))
    shutil.copy(BUNDLED / "01_alpha.json", tmp / "01_alpha.json")
    shutil.copy(BUNDLED / "02_beta.json", tmp / "02_beta.json")
    shutil.copy(TB3_SRC / "03_gamma.json", tmp / "03_gamma.json")
    return tmp


def test_tb3_three_segment_hidden_merge():
    """Hidden third segment with overlapping deletes must match reference."""
    seg_dir = _tb3_dir()
    try:
        _pipeline(seg_dir)
        got = json.loads(STATS.read_text(encoding="utf-8"))
        ref = reference_stats(STAGE)
        assert got["live_max_doc"] == ref["live_max_doc"] == 12
        assert got["delete_bits"] == ref["delete_bits"]
        assert got["terms"] == ref["terms"]
    finally:
        shutil.rmtree(seg_dir, ignore_errors=True)


def test_tb3_segment_seed_permutes_doc_ids():
    """TB3_SEGMENT_SEED permutes local doc ids before global remap."""
    seg_dir = _tb3_dir()
    try:
        _fresh()
        _ingest(seg_dir)
        _run(
            [TANTICTL, "merge", "export"],
            env={"TB3_SEGMENT_SEED": "2"},
        )
        got = json.loads(STATS.read_text(encoding="utf-8"))
        ref = reference_stats(STAGE, seed=2)
        assert got["delete_bits"] == ref["delete_bits"]
        assert got["live_max_doc"] == ref["live_max_doc"]
    finally:
        shutil.rmtree(seg_dir, ignore_errors=True)


def test_tb3_hidden_checksum_with_seed():
    """Hidden fixture checksum matches reference under TB3_SEGMENT_SEED."""
    seg_dir = _tb3_dir()
    try:
        _fresh()
        _ingest(seg_dir)
        _run(
            [TANTICTL, "merge", "export"],
            env={"TB3_SEGMENT_SEED": "3"},
        )
        digest = CHECKSUM.read_text(encoding="utf-8").strip()
        assert digest == reference_checksum(STAGE, seed=3)
    finally:
        shutil.rmtree(seg_dir, ignore_errors=True)


def test_tb3_idempotent_second_pass_hidden():
    """Hidden three-segment merge stays idempotent on pass 2."""
    seg_dir = _tb3_dir()
    try:
        _pipeline(seg_dir)
        first = CHECKSUM.read_text(encoding="utf-8").strip()
        _export(2)
        second = CHECKSUM.read_text(encoding="utf-8").strip()
        assert second == first
    finally:
        shutil.rmtree(seg_dir, ignore_errors=True)
