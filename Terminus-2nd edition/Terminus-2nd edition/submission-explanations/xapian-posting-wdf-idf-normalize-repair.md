# Submission explanations — xapian-posting-wdf-idf-normalize-repair

**Task folder:** tasks/xapian-posting-wdf-idf-normalize-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is hard because six Rust modules must agree on Xapian-style WDF-IDF math spread across five contract documents, not a single obvious formula typo. The broken collector counts raw tokens instead of collapsed slots, cf_table inflates collection frequency per occurrence, length normalization uses total token length, synonym expansion sums alternate WDFs, and OR-branch scoring drops IDF for terms below TB3_RARE_CF. Ingest also persists the live index before writing the staging snapshot, so ordering bugs survive even when query scores look close on one fixture. Partial repairs pass bundled tech-rust or dup-collapse batches yet still fail hidden traps where adjacent duplicate collapse, synonym max-aggregation, rare-term IDF, or docid tie-breaking matter independently. Decoy posting-merge and tokenizer helpers stay off the hot path, so agents who patch the wrong crate never reach export scoring.

## Solution Explanation

The oracle copies golden implementations into the six repair-scope modules listed in /app/docs/repair-scope.md, then rebuilds xapian-weight-cli with cargo build --release --locked. collector.rs derives WDF from collapsed slot counts via slot_counts, cf_table.rs counts each document once per unique collapsed term, and norm.rs normalizes by the square root of distinct collapsed terms. expand.rs aggregates synonym WDF with max rather than sum, or_branch.rs always multiplies effective WDF by full IDF on OR queries, and store.rs writes /app/state/index-staging.json with written_before_index true before saving /app/work/index.json. The rebuilt binary is installed to /usr/local/bin/xapian-weight-cli and reset-state.sh clears work and output directories for a clean verifier run.

## Verification Explanation

Pytest rebuilds the workspace in test.sh, then drives xapian-weight-cli index and query through subprocess on bundled JSONL batches. An independent reference_xapian_weight.py recomputes collapsed WDF, collection frequency, length normalization, synonym effective WDF, and ranked hit lists so hard-coded JSON cannot pass. Tests assert staging snapshot fields including batch_sha256 and written_before_index, persisted cf tables after ingest, AND query filtering, and SHA256 integrity of protected docs, fixtures, and CLI entrypoints. Hidden batches under /opt/verifier-fixtures exercise positional collapse WDF, synonym max-not-sum scoring, equal-score docid tie-breaking, and TB3_RARE_CF environment overrides on rare OR terms. Parametrized bundled queries compare rounded docid-score tuples against the reference pipeline on every catalog batch.
