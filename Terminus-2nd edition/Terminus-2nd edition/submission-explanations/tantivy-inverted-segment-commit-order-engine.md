# Submission explanations — tantivy-inverted-segment-commit-order-engine

**Task folder:** tasks/tantivy-inverted-segment-commit-order-engine/
**Platform form only** — not in upload zip.
**Updated:** 2026-06-27T04:12:39Z

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked hard because the agent must wire a Rust ingest-to-search pipeline where staging merge, WAL commit order, and export disagree unless several modules align. Contracts live across /app/docs/wal-barrier.md, /app/docs/merge-commit-order.md, and /app/docs/index-pipeline.md, so fixing only posting remap or only search export still fails hidden checks. Search must read committed segment ids, not staging lanes, which is easy to miss when bundled fixtures look fine after a one-file patch. TB3_INDEX_PREFIX builds absolute index namespaces, so path handling must match the docs, not just the default corpus name. Frontier models tend to stop after the first obvious bug in one module even though 18 behavioral tests require the full contract to line up.

## Solution Explanation

The oracle copies corrected sources (scheduler.rs, finalize.rs, norm.rs, wal.rs, search.rs) into /app, rebuilds tantool, and runs the documented CLI end-to-end. The main insight is to remap posting doc ids with segment offsets before merge, evict obsolete staging ids from reader_registry, and count live docs only after tombstone exclusion at finalize. WAL fsync must complete before the commit lock releases, with lock_released_before_fsync staying false on success. Search export walks committed_segment_ids and writes JSON hit arrays without re-tokenizing JSONL fixtures. Field norms on merged segments must use canonical title=1 and body=2 ids from the norm table docs.

## Verification Explanation

Pytest (18 cases) rebuilds tantool with cargo in test.sh, then drives the CLI via subprocess with fresh output paths per test. An independent reference_index module recomputes expected hits, live counts, and posting checksums from the same fixtures cited in instruction.md, so hard-coded reports cannot pass. Dedicated tests assert index-catalog.json, index-snapshot.json, wal-record.json, and wal marker files after commit. Hidden verifier fixtures under /opt/verifier-fixtures/tantivy-segments exercise search on a two-segment corpus that bundled trees alone do not cover. TB3_INDEX_PREFIX tests catch export and ingest paths that only work on the default corpus index name.
