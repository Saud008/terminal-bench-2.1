# Submission explanations — udp-input-frame-ack-gap-ledger-reconciler

**Task folder:** tasks/udp-input-frame-ack-gap-ledger-reconciler/
**Platform form only** — not in upload zip.
**Updated:** 2026-07-29T20:40:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note (ESCALATED — do not refile):** Graded work is diagnosing and fixing planted bugs across framecore modules (naive `a < b` seq compare, big-endian `loss_mask`, incremental gap append plus ingest-time peer-loss merge, naive playhead origin, min/max staging normalization, dup-skip ingest, decoy `merge_ranges_legacy` on the publish path) so behavior matches the docs. That is debugging activity, not build-system or dependency work. Harbor currently hard-blocks `category = "debugging"`, and swapping to another open category solely to clear the block is rejected. Leave `category = "build-and-dependency-management"` in the zip for now and keep the taxonomy mismatch escalated to the team for where bug-fix tasks should live.

**Ignore (automated noise):** Keep the pinned `public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe…` base image; leave `difficulty = "medium"` (measured worst-model pass rate, not wall-clock/file-count); do not document `client_id` — `seed_client_id` already ships in non-buggy `replay/mod.rs` and parity follows from fixing bugs rather than rewriting the pipeline.

## Difficulty Explanation

Agents must wire a two-stage udpctl pipeline where ingest writes /app/state/replay-staging.json and export reads that snapshot before merging gap ranges. Bugs span wire parsing, u32 sequence math, ledger recompute, sim tick application, staging persistence, export-time merge rules, and ingest duplicate handling spread across five docs and multiple framecore modules. Fixing only export publish or only ledger playhead still fails loss-bitmask peer tuples, duplicate resend sim parity, partial tick batches, or hidden verifier bundles. Partial fixes that normalize descending peer-loss tuples pass some bundled replays but fail staging contract tests and hidden traps.

## Solution Explanation

The oracle copies nine golden patches into framecore modules covering wire seq and parser, ledger gap and playhead, sim tick, staging write, export publish, and ingest run. It rebuilds udpctl with cargo and leaves the broken decoy wrap.rs unused. Ingest must recompute received gaps from the full seen set and append raw peer-loss tuples without min-max normalization. Export performs one lexicographic merge on staged gaps_raw and peer_loss_raw when writing the replay report JSON.

## Verification Explanation

test.sh resets /app/state and /app/output, rebuilds udpctl, then runs 25 pytest cases via subprocess CLI calls. reference_replayer.py independently recomputes staging snapshots and export JSON from bundle hex. Tests cover ingest-only staging bytes, split ingest plus export parity with replay, explicit output and staging paths, and two hidden bundles under /tests/hidden_fixtures with optional verifier fixture overrides. NOP on the seeded broken baseline fails most behavioral tests. Oracle patches yield reward 1.
