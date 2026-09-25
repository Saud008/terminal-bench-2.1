# Submission explanations — mantidx-rt-killlist-rotate-engine

**Task folder:** tasks/mantidx-rt-killlist-rotate-engine/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents implement a Rust RT index CLI with rotate killlist ordering, binlog checkpoint commit, scoped killlist merge, RAM segment merge bitmap handling, attribute updates on killed docs, and search consistency. Contracts live across six docs under /app/docs without a single recipe. Rotate must target the newest active_ram entry, apply killlist before disk publish, and emit killlist-merge-audit merged_order in segment_order then doc_id order. Hidden batches load through TB3_DOCS_DIR from verifier-only fixtures and punish fixes that only touch rotate.rs. Partial fixes pass bundled checks but fail hidden tombstone or pending killlist traps.

## Solution Explanation

The oracle copies patched rotate.rs, binlog.rs, killlist.rs, ram_merge.rs, attribute.rs, and search.rs into mantidx-core, runs cargo build locked release, and installs mantidx. Rotate applies killlist on the newest active RAM segment before tier reassignment and commits all binlog_pending rows. Killlist merge sorts by segment order then doc id, scopes to the rotating segment, and writes merged_order in killlist-merge-audit.json. Merge ram unions deleted bitmaps and marks docs killed while search and attribute modules skip killed documents.

## Verification Explanation

Subprocess CLI checks cover rotate audit JSON, binlog checkpoint sequences, killlist-merge-audit merged_order against an independent reference sort, merge audits, attribute rejection, absolute TB3_DOCS_DIR overrides, and hidden rotate_kill.jsonl staged outside the agent image. Seven behavioral tests span rotate, killlist scoping, merge ram, attribute, search, and hidden batch traps; oracle reward is one when patches are applied.
