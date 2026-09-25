# Submission explanations — go-prometheus-remote-write-histogram-exemplar-staging

**Task folder:** tasks/go-prometheus-remote-write-histogram-exemplar-staging/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task builds a Prometheus remote-write ingest service with a disk staging layer between decode and snapshot export. I rated it hard because checksum validation, schema preservation, staging sequence tracking, relabel deduplication, and exemplar binding live in separate modules and docs. Fixing ingest alone still leaves export reading stale in-memory state or wrong staging bytes. Hidden seeds under the verifier fixture directory use reversed exemplar order and different bucket bounds, so round-robin binding passes bundled tests but fails those traps. Partial fixes on one file leave nine of ten platform runs green, which is why agents still pass too easily without the full pipeline.

## Solution Explanation

The oracle copies corrected Go sources for decode, staging persist, server routing, relabel, and exemplar bind, then rebuilds promingest and promenc. Write handling must only decode and persist staging JSON under /app/data/ingest. Snapshot export reads that file, applies relabel and exemplar binding, and returns the staging sequence. The key insight is that export-only fixes never touch staging schema or sequence, and ingest-only fixes never run relabel at export time.

## Verification Explanation

test.sh rebuilds both Go binaries before pytest. Twenty three tests POST remote-write blocks to the HTTP server and compare snapshots against an independent Python reference. Tests assert staging file paths, sequence increments on double writes, checksum rejection without staging artifacts, and hidden fixture seeds from /opt/verifier-fixtures. The reference recompute blocks pasted JSON answers. NOP on the broken baseline scores zero. After the oracle patches and rebuild, all tests pass.
