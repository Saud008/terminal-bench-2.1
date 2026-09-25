# Submission explanations — ansible-facts-jsonl-reconciler

**Task folder:** tasks/ansible-facts-jsonl-reconciler/
**Platform form only** — not in upload zip.

## Difficulty Explanation

The Ansible facts reconciler at /app ingests JSONL batches into SQLite, writes a staging snapshot, and exports a diff report per run. Agents struggle because behavior is split across jsonl-format.md, staging-format.md, export-format.md, and invariants.md while bugs live in several shell modules. Partial fixes often pass merge checks but still fail export diff rows, staging validation, or idempotent reconcile counts. The starter code can emit null old values on changed facts while counts look correct. Cross-run diff value tests and distinct inventory_uuid cases catch shallow one-file patches.

## Solution Explanation

The oracle copies corrected lib and stage scripts into /app and runs make install. Reconcile must validate each JSONL line before SQLite mutation, merge facts by inventory_uuid with latest collected_at wins, and record fact_diffs only when values change using stringified JSON scalars for old and new fields. Stage builds facts.staging.json only after schema validation against facts.db. Export reads fact_diffs for the run id and writes changed_key_count, changed_keys_digest, and sorted diff_rows. INSERT OR IGNORE on fact_diffs keeps a second reconcile with the same run id from duplicating rows.

## Verification Explanation

test.sh runs make install then pytest with an independent reference_facts module that recomputes merge, staging hosts, changed key digests, and expected diff rows from JSONL fixtures. Tests drive /app/bin/facts-chain reconcile, stage, and export via subprocess against /app/state/facts.db, /app/state/facts.staging.json, and /app/output/facts-diff.json. A dedicated test asserts exported diff rows include correct old and new values for changed facts across two reconcile runs. NOP on the broken baseline should score zero. After the oracle patches, all behavioral tests pass.
