# Submission explanations - subtitle-srt-rollup-ruby-normalize

**Task folder:** tasks/subtitle-srt-rollup-ruby-normalize/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-10T11:26:16Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Operators must build a two-stage temporal closure pipeline so srtctl normalize publishes caption exports and sealed snapshot artifacts from bundled SRT logs. I rated it hard because overlap trim, ruby timing caps, roll-up space joins, ledger digest sealing, and monotonic export sequence interact across stage 1 and stage 2. Fixing one module can pass bundled fixtures while procedural combo seeds, hidden traps, or repeat-run sequence checks still fail. Partial stage-1 order fixes leave export reading the wrong cue source. About two dozen pytest cases recompute reference math independently, so shallow single-file patches rarely survive the full contract surface.

## Solution Explanation

The oracle copies corrected Rust modules into srt-core, rebuilds srtctl offline, and runs normalize against the same fixtures agents see. Stage 1 must persist post-ruby cues in normalize-snapshot.json and seal normalize-ledger.json before stage 2 reads staged cues only. Key insight is stage order overlap before ruby, ledger snapshot_digest over raw snapshot bytes, and export_seq driven by the marker file while repeat exports stay byte identical. Roll-up must join absorbed cue text with a single ASCII space and preserve ruby segments on merged rows.

## Verification Explanation

test.sh runs cargo build before pytest on every verifier pass. Pytest invokes srtctl normalize via subprocess and compares export JSON, snapshot files, and ledger fields to an independent Python reference implementation. Tests cover bundled fixtures, procedural seeds generated at runtime, and hidden inputs under the verifier fixtures mount. Staging and ledger sealing assertions run before export shape checks. NOP on the broken baseline should score zero. After the oracle applies its module patches and rebuild, the full suite should pass.
