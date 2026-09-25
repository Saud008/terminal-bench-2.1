# Submission explanations — subtitle-srt-rollup-ruby-timing-repair

**Task folder:** tasks/subtitle-srt-rollup-ruby-timing-repair/
**Platform form only** — not in upload zip.
**Updated:** 2026-06-26T00:45:00Z

> Short plain-English paragraphs for the Snorkel upload form. Tweak so it sounds like you.

## Difficulty Explanation

Agents must implement a two-stage SRT normalize pipeline in Rust where stage one writes a snapshot and sealed ledger and stage two exports roll-up JSON from that staged state only. The hard part is overlap trim must run before ruby segment caps, roll-up must space-join text while keeping ruby segments, and the ledger must seal raw snapshot bytes plus a monotonic export sequence across repeat runs. Bundled fixtures exercise each rule separately but procedural and hidden traps combine overlap, ruby, roll-up, and digest sealing in one file. Fixing publish alone still passes some bundled rows because broken_lib legacy re-parses the source SRT until agents wire every stage.

## Solution Explanation

The oracle copies golden Rust modules into srt-core, rebuilds srtctl with cargo, and runs the same normalize CLI pytest uses. Stage one parses, offsets, trims overlaps, applies ruby shifts, then writes normalize-snapshot.json and normalize-ledger.json with a correct snapshot_digest and export_seq. Stage two publish validates the ledger, reads staged cues, and export applies roll-up before writing JSON. Export bytes stay identical on repeat normalize while export_seq increments via the marker file. Legacy single-pass helpers and decoy ingest modules stay off the hot path.

## Verification Explanation

test.sh runs cargo build before pytest. About 31 tests call srtctl normalize via subprocess and compare exports to an independent Python reference_srt implementation. Tests cover snapshot and ledger paths, idempotent export bytes, export_seq increments, procedural combo seeds, partial-fix traps that swap one broken module back in, and three hidden fixtures under /opt/verifier-fixtures/srtctl. NOP on the broken image should score zero. After the oracle patches and rebuild, the full suite passes.
