"""
Verifier for tantool inverted segment merge, commit WAL, and search export.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from reference_index import (
    live_doc_count,
    pipeline_from_batches,
    posting_checksum,
    search_term,
)

APP = Path("/app")
CLI = "/usr/local/bin/tantool"
OUT = Path("/app/output")
STATE = Path("/app/state")
RESET = APP / "scripts/reset-state.sh"
FIX_A = APP / "fixtures/segment_a.jsonl"
FIX_B = APP / "fixtures/segment_b.jsonl"
HIDDEN = Path("/opt/verifier-fixtures/tantivy-segments")
SNAPSHOT = Path("/app/state/index-snapshot.json")
CATALOG = Path("/app/state/index-catalog.json")
WAL_RECORD = Path("/app/state/wal-record.json")
SEARCH_HITS = Path("/app/output/search-hits.json")
WAL_MARKER_PREFIX = "/app/state/wal-"
INSTRUCTION_OUTPUT_PATHS = (
    "/app/output/search-hits.json",
    "/app/state/index-catalog.json.",
    "/app/state/index-snapshot.json.",
    "/app/state/wal-",
    "/app/state/wal-record.json",
)


def _run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
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


def _ingest(index: str, batch: Path, env: dict[str, str] | None = None) -> None:
    proc = _run([CLI, "ingest", "--index", index, "--input", str(batch)], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def _merge(index: str, env: dict[str, str] | None = None) -> None:
    proc = _run([CLI, "merge", "--index", index], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def _commit(index: str, env: dict[str, str] | None = None) -> None:
    proc = _run([CLI, "commit", "--index", index], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def _search(index: str, field: str, term: str, out: Path, env: dict[str, str] | None = None) -> list[int]:
    proc = _run(
        [CLI, "search", "--index", index, "--field", field, "--term", term, "--out", str(out)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def _stats(index: str, env: dict[str, str] | None = None) -> dict:
    proc = _run([CLI, "stats", "--index", index], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout.strip())


def _full_pipeline(index: str = "corpus") -> None:
    _ingest(index, FIX_A)
    _ingest(index, FIX_B)
    _merge(index)
    _commit(index)


def test_bundled_search_title_rust() -> None:
    """Committed search for title term rust must match reference merged postings."""
    _reset()
    _full_pipeline()
    ref = pipeline_from_batches([FIX_A, FIX_B])
    hits = _search("corpus", "title", "rust", OUT / "rust.json")
    assert hits == search_term(ref, "title", "rust")


def test_bundled_search_excludes_tombstoned_tantivy() -> None:
    """Tombstoned docs stay out of search hits while live committed search still works."""
    _reset()
    _full_pipeline()
    ref = pipeline_from_batches([FIX_A, FIX_B])
    rust_hits = _search("corpus", "title", "rust", OUT / "rust_tomb_gate.json")
    assert rust_hits == search_term(ref, "title", "rust")
    assert rust_hits == [0]
    hits = _search("corpus", "title", "tantivy", OUT / "tantivy.json")
    assert hits == search_term(ref, "title", "tantivy")
    assert hits == []


def test_bundled_search_body_checksum_lane() -> None:
    """Body search for checksum must return live delta merge doc id."""
    _reset()
    _full_pipeline()
    ref = pipeline_from_batches([FIX_A, FIX_B])
    hits = _search("corpus", "body", "checksum", OUT / "checksum.json")
    assert hits == search_term(ref, "body", "checksum")


def test_live_doc_count_matches_reference() -> None:
    """Stats live_doc_count must equal reference live count after merge finalize."""
    _reset()
    _full_pipeline()
    ref = pipeline_from_batches([FIX_A, FIX_B])
    stats = _stats("corpus")
    assert stats["live_doc_count"] == live_doc_count(ref)


def test_posting_checksum_matches_reference() -> None:
    """Stats posting_checksum must match independent reference over committed segment."""
    _reset()
    _full_pipeline()
    ref = pipeline_from_batches([FIX_A, FIX_B])
    stats = _stats("corpus")
    assert stats["posting_checksum"] == posting_checksum(ref)


def test_no_dangling_readers_after_merge() -> None:
    """Obsolete staging segments must not remain in reader_registry after merge."""
    _reset()
    _full_pipeline()
    stats = _stats("corpus")
    assert stats["dangling_reader_count"] == 0


def test_wal_barrier_order() -> None:
    """Commit must not release lock before WAL fsync marker is written."""
    _reset()
    _full_pipeline()
    stats = _stats("corpus")
    assert stats["wal_fsynced"] is True
    assert stats["commit_lock_released_before_wal"] is False


def test_field_norms_canonical() -> None:
    """Merged segment field norms must use canonical title=1 body=2 ids."""
    _reset()
    _full_pipeline()
    stats = _stats("corpus")
    assert stats["field_norm_title"] == 1
    assert stats["field_norm_body"] == 2


def test_search_reads_committed_not_staging() -> None:
    """Search after ingest without merge must not expose staging postings."""
    _reset()
    _ingest("corpus", FIX_A)
    hits = _search("corpus", "title", "rust", OUT / "pre_merge.json")
    assert hits == []


def test_snapshot_matches_stats() -> None:
    """index-snapshot.json must match reference metrics and agree with stats output."""
    _reset()
    _full_pipeline()
    ref = pipeline_from_batches([FIX_A, FIX_B])
    stats = _stats("corpus")
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["live_doc_count"] == live_doc_count(ref)
    assert snap["posting_checksum"] == posting_checksum(ref)
    assert snap["dangling_reader_count"] == 0
    assert stats["live_doc_count"] == snap["live_doc_count"]
    assert stats["posting_checksum"] == snap["posting_checksum"]
    assert stats["dangling_reader_count"] == snap["dangling_reader_count"]


def test_hidden_tb3_fixture_search() -> None:
    """Hidden two-segment corpus under /opt must match reference search hits."""
    _reset()
    hidden_a = HIDDEN / "tb3_hidden_a.jsonl"
    hidden_b = HIDDEN / "tb3_hidden_b.jsonl"
    assert hidden_a.is_file() and hidden_b.is_file()
    index = "tb3_hidden"
    _ingest(index, hidden_a)
    _ingest(index, hidden_b)
    _merge(index)
    _commit(index)
    ref = pipeline_from_batches([hidden_a, hidden_b])
    hits = _search(index, "title", "zeta", OUT / "hidden_zeta.json")
    assert hits == search_term(ref, "title", "zeta")


def test_tb3_index_prefix_absolute() -> None:
    """TB3_INDEX_PREFIX builds absolute index namespace for ingest and search."""
    _reset()
    prefix = "/app/data/tb3_lane"
    index = "lane"
    env = {"TB3_INDEX_PREFIX": prefix}
    _ingest(index, FIX_A, env=env)
    _ingest(index, FIX_B, env=env)
    _merge(index, env=env)
    _commit(index, env=env)
    ref = pipeline_from_batches([FIX_A, FIX_B])
    hits = _search(index, "title", "wal", OUT / "tb3_wal.json", env=env)
    assert hits == search_term(ref, "title", "wal")


def test_second_commit_idempotent_stats() -> None:
    """Re-commit on unchanged catalog must keep reference live_doc_count stable."""
    _reset()
    _full_pipeline()
    ref = pipeline_from_batches([FIX_A, FIX_B])
    first = _stats("corpus")
    assert first["live_doc_count"] == live_doc_count(ref)
    _commit("corpus")
    second = _stats("corpus")
    assert second["live_doc_count"] == live_doc_count(ref)
    assert first["live_doc_count"] == second["live_doc_count"]


def test_instruction_output_paths_written() -> None:
    """Covers /app/output/search-hits.json and /app/state index-catalog snapshot wal-record paths."""
    assert INSTRUCTION_OUTPUT_PATHS == (
        "/app/output/search-hits.json",
        "/app/state/index-catalog.json.",
        "/app/state/index-snapshot.json.",
        "/app/state/wal-",
        "/app/state/wal-record.json",
    )
    _reset()
    _full_pipeline()
    ref = pipeline_from_batches([FIX_A, FIX_B])
    hits = _search("corpus", "title", "rust", SEARCH_HITS)
    assert hits == search_term(ref, "title", "rust")
    assert SEARCH_HITS.is_file()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    corpus = catalog["indexes"]["corpus"]
    assert corpus["staging_segment_ids"] == []
    assert len(corpus["committed_segment_ids"]) == 1
    assert corpus["committed_live_docs"] == live_doc_count(ref)

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["index"] == "corpus"
    assert snap["live_doc_count"] == live_doc_count(ref)

    wal = json.loads(WAL_RECORD.read_text(encoding="utf-8"))
    assert wal["index"] == "corpus"
    assert wal["wal_fsynced"] is True
    assert wal["lock_released_before_fsync"] is False

    wal_marker = Path(f"{WAL_MARKER_PREFIX}corpus.marker")
    assert wal_marker.is_file()
    assert wal_marker.read_text(encoding="utf-8").strip() == str(live_doc_count(ref))


def test_pre_merge_staging_segment_count() -> None:
    """Two ingests must leave exactly two staging segments before merge runs."""
    _reset()
    _ingest("corpus", FIX_A)
    _ingest("corpus", FIX_B)
    stats = _stats("corpus")
    assert stats["staging_segments"] == 2
    assert stats["committed_segments"] == 0


def test_staging_cleared_after_commit() -> None:
    """Merge and commit must clear staging segments from catalog stats."""
    _reset()
    _full_pipeline()
    stats = _stats("corpus")
    assert stats["staging_segments"] == 0
    assert stats["committed_segments"] == 1


def test_catalog_obsolete_segments_recorded() -> None:
    """Merge must record both source staging ids in obsolete_segment_ids."""
    _reset()
    _full_pipeline()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    obsolete = catalog["indexes"]["corpus"]["obsolete_segment_ids"]
    assert len(obsolete) == 2


def test_snapshot_segment_count_matches_stats() -> None:
    """index-snapshot.json segment_count must match stats committed segment tally."""
    _reset()
    _full_pipeline()
    stats = _stats("corpus")
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["segment_count"] == stats["committed_segments"]
    assert snap["segment_count"] == 1
