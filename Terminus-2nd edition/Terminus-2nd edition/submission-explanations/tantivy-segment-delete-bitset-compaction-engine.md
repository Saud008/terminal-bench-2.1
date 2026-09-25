# Submission explanations — tantivy-segment-delete-bitset-compaction-engine

**Task folder:** tasks/tantivy-segment-delete-bitset-compaction-engine/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a Rust tantictl compaction governor with ingest staging, a separate merge engine, and an export stats path. The hard part is ordering doc id remap before delete bitset union, subtracting tombstone hits from term frequencies, exporting the union max_doc across segment doc spaces, keeping u8 norm encoding in the stats JSON, and making a second merge pass idempotent. Contracts are split across six docs under /app/docs/, so agents cannot infer behavior from the short instruction alone. Fixing only remap order or only freq math still leaves norms, live_max_doc, or idempotency wrong. Hidden verifier fixtures add a third segment and TB3_SEGMENT_SEED local doc id permutation, which breaks naive OR-without-offset or raw freq summation approaches.

## Solution Explanation

The oracle patches merge bitset, freq rollup, live max doc stats, posting norm export, and export idempotency modules, then rebuilds tantictl with cargo. Merge reads the staging snapshot only, applies seed based local id remap per delete-bitset-remap.md, unions global tombstones, and rolls up live term counts after tombstone subtraction. Live max doc becomes the sum of segment max_doc values, and posting norms serialize as u8 width JSON numbers. Pass two must reuse prior merge state without re-accumulating delete bits, matching merge-idempotency.md. The canonical checksum derives from compact stats JSON with merge_pass zeroed, not from pretty printed file text.

## Verification Explanation

Pytest drives tantictl through subprocess for every behavioral check. An independent reference_merge module recomputes expected stats and checksum from staging JSON. Bundled two segment fixtures exercise the main contracts. Hidden tests add a third segment from verifier fixtures and set TB3_SEGMENT_SEED to permute local doc ids. test.sh rebuilds the Rust binary before pytest so agents cannot pass with a stale image binary.
