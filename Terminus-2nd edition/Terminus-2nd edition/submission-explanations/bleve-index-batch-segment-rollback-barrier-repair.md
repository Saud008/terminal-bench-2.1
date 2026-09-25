# Submission explanations — bleve-index-batch-segment-rollback-barrier-repair

**Task folder:** tasks/bleve-index-batch-segment-rollback-barrier-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must repair a Rust blevectl ingest/export control plane where FNV-1 vs FNV-1a checksum admission, unlisted collator ranking, open-batch disk fences, and merge-plan segment lists interact across writer, store, checksum, scheduler, allocator, and export modules. The seeded checksum path intentionally implements FNV-1a while fixtures and docs require FNV-1 (multiply then xor), and the decoy zap_wrap helper also exposes FNV-1a. Collator near-misses that collapse unlisted keys onto rank 0 pass listed-only intuition but fail mixed key fixtures. Merge scheduling must clear and observe on-disk open-batch.flag, enforce a two-segment threshold, and emit a segments[] field matching the root map. Partial fixes that only invert an obvious boolean or patch export still leave rollback traps, counter advances, or merge-plan shape failures.

## Solution Explanation

The oracle installs corrected Rust sources for writer, store, checksum, scheduler, allocator, key order, and export stage, then rebuilds blevectl with cargo. Ingest verifies FNV-1 checksums before committing segments, rolls back root-map pointers on failure, commits doc ids only after success, clears the open-batch flag, and only then schedules merge when at least two segments exist. Export rejects missing segment files and sorts keys with unlisted ranks after every listed key. The decoy zap_wrap module is not on the hot path.

## Verification Explanation

test.sh runs cargo build before pytest. Tests invoke blevectl through subprocess with an isolated index prefix and compare results to an independent reference_bleve_index module that recomputes FNV-1 and collator order. Bundled and hidden fixtures cover checksum rollback, unlisted-key collator order, staging snapshot status, merge-plan absence after one ingest, merge-plan segments[] after two ingests, FNV-1a near-miss rejection, and export consistency when rollback traps fire. Protected docs and the decoy file must remain unchanged. Oracle passes all tests after patching and rebuild. NOP on the seeded image scores zero.
