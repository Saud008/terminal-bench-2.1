# Submission explanations — cdc-chunk-boundary-merkle-roll-forward-repair

**Task folder:** tasks/cdc-chunk-boundary-merkle-roll-forward-repair/
**Platform form only** — not in upload zip.
**Updated:** 2026-06-29T14:05:00Z

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked hard because cdcctl roll must implement content-defined chunking, a merkle root over chunk hashes, and resumable checkpoints as one coupled Go pipeline spread across five internal packages. The contract lives in roll-contract.md, merkle-tree.md, and fixture-catalog.md, including seed-derived CDC parameters, ASCII-hex merkle pairing with odd-leaf duplication of the last node, and precise checkpoint offset semantics for --max-chunks and --resume. Fixing only the rolling hash or only merkle pairing can make baseline rolls look correct while resume, double-resume, and fresh-roll-ignores-stale-checkpoint cases still fail. Agents often patch merkle/tree.go or chunk/cdc.go in isolation and miss config byte indexing, checkpoint window serialization, or engine logic that wrongly auto-resumes from a complete checkpoint without the --resume flag. Twenty-one behavioral tests require every layer to agree byte-for-byte with an independent reference simulator, not just the first fixture in the catalog.

## Solution Explanation

The oracle replaces all five broken internal modules—config, chunk, merkle, checkpoint, and roll—with golden implementations, then rebuilds cdcctl via go build. Config must derive min_chunk, max_chunk, and target from the correct SHA-256 digest byte indices for each seed. CDC must left-shift the rolling window hash, evaluate boundaries only after pushing the current byte, enforce min_chunk before mask hits, and build chunk IDs from seed, offset, and bytes. Merkle parents hash the UTF-8 concatenation of sibling hex strings, duplicating the last leaf when the level is odd. Checkpoint save must persist the base64 rolling window and restore chunk_start separately from offset, while the roll engine only loads prior state on --resume, counts new chunks for --max-chunks limits, and writes offset as the next unread byte when stopping mid-stream.

## Verification Explanation

Pytest rebuilds the Go binary in test.sh, then drives /usr/local/bin/cdcctl roll through subprocess with isolated output and checkpoint paths per case. An independent reference_roll.py module recomputes the full JSON report, phased checkpoints, and merkle roots from the same fixtures and seeds, so agents cannot hard-code answers. Bundled tests cover representative fixture-seed pairs, odd-leaf merkle trees, injected single-byte mutations, and min-chunk boundary deferral. Anti-cheat cases assert partial --max-chunks rolls skip the output file, resume eventually matches a one-shot reference, checkpoint window and chunk_start match simulate_roll, and different seeds partition the same fixture differently. Together these checks enforce CLI-only behavior across fresh rolls, multi-phase resume, and checkpoint persistence without relying on source-file swaps.
