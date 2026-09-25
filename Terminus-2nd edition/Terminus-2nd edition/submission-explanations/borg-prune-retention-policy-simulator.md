# Submission explanations — borg-prune-retention-policy-simulator

**Task folder:** tasks/borg-prune-retention-policy-simulator/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a Borg-style retention dry-run simulator where ingest, evaluate, and export share a staging file beside the list fixture. Legal holds, clock-skewed snapshot timestamps, weekly bucket boundaries, and duplicate archive names interact so fixing only list parsing or only export compaction still fails most checks. Contracts live in /app/docs/retention-buckets.md, /app/docs/legal-holds.md, and /app/docs/clock-skew.md rather than in a single recipe in the instruction. Partial fixes often pass bundled smoke but fail hidden /opt/verifier-fixtures cases that combine skewed timestamps with prefix holds. Frontier models frequently stop after correcting compaction sums while leaving staging path and duplicate-resolution bugs in place.

## Solution Explanation

The oracle replaces six Bash modules: common staging path resolution, tab-separated list parsing with last-line-wins duplicates, clock-skew clamping, prefix-start legal holds, policy-aware weekly buckets, and export compaction totals from pruned archives only. Ingest writes archives and repo_id to dirname(list)/borg.stage.json. Evaluate adds the evaluation block with bucket hits and hold survivors. Export reads that block and emits sorted compact JSON with reclaimable byte and segment totals. The workflow is intentionally multi-file because decoy legacy prune helpers are off the hot path.

## Verification Explanation

Twenty pytest functions rebuild the CLI via make install, then run borg-prune-sim through subprocess on seed, randomized, and hidden fixtures. reference_retention.py independently parses list files and computes kept versus pruned sets without reading agent source. Tests assert exact export JSON formatting, staging beside custom list paths, and TB3 hidden skew and holds directories baked into the image at build time. Randomized archive timestamps and policy windows block hard-coded prune lists. NOP on the broken baseline fails while the patched oracle passes all twenty tests.
