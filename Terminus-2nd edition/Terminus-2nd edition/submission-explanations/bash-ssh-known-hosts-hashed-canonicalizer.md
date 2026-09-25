# Submission explanations — bash-ssh-known-hosts-hashed-canonicalizer

**Task folder:** tasks/bash-ssh-known-hosts-hashed-canonicalizer/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire five bash modules for a two-stage known_hosts pipeline. Ingest appends JSONL ledger rows and seals a manifest bound to input bytes. Export merges staged records and emits normalized lines with marker, bracket, and hashed-field rules that interact. Bracketed host_sort_key must strip brackets and port suffix. Fixing parse without merge sort or export markers passes most catalog fixtures but fails mixed ordering and hidden traps. The decoy sort helper sorts by key blob and is not authoritative.

## Solution Explanation

The oracle copies golden parse, ledger, merge, emit, and decoy modules into /app/lib subdirectories, then resets state. Parse handles markers, hashed segments, and plain host normalization. Ledger writes seq-stamped JSONL and seals manifest digests from file bytes. Merge applies duplicate policy and contract sort tuples. Emit preserves revoked and cert-authority markers and comments on output lines.

## Verification Explanation

test.sh runs rebuild-libs.sh then pytest against twenty behavioral tests. Each test invokes kh-normalize via subprocess and compares output to reference_normalize. Hidden tests under /opt/verifier-fixtures exercise bracket sort order, merge_duplicates false config, and export comment preservation traps independent from catalog fixtures. Ledger and staging tests assert JSONL snapshot shape and manifest binding after ingest.
