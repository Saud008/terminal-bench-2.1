Task identity 8a3f2e1b defines the engineering problem for go clickhouse partition mutation ledger. See /app/docs/engineering-problem-contract.md for scope and verifier contracts.

# Partition mutation readiness ledger

Extend the working Go service at /app so chmutled reconciles ClickHouse-style partition mutation state offline. Agents ingest partition metadata catalogs, mutation command journals, and replica lag transcripts, then emit staging rows, a SQLite ledger, and a mutation readiness atlas per the contracts in /app/docs/.

## Contracts

Consult the /app/docs/ contracts listed below.

| Topic | File |
|-------|------|
| CLI verbs and flags | /app/docs/cli_surface.md |
| Partition metadata rows | /app/docs/partition_metadata_format.md |
| Mutation command rows | /app/docs/mutation_command_format.md |
| Replica lag transcripts | /app/docs/replica_log_format.md |
| Partition key canonicalization | /app/docs/partition_key_normalization.md |
| Mutation version ladder | /app/docs/mutation_version_ordering.md |
| Lag suppression policy | /app/docs/replica_lag_suppression.md |
| Detached part exclusion | /app/docs/detached_part_handling.md |
| Reconcile staging layout | /app/docs/staging_pipeline.md |
| Readiness atlas export | /app/docs/mutation_readiness_export.md |

## Runtime layout

Binary: /app/bin/chmutled

| Verb | Primary outputs |
|------|-----------------|
| reconcile-partitions | /app/state/chledger-staging.jsonl |
| emit-readiness | /app/output/mutation-readiness-atlas.json and /app/output/chledger-rows.sqlite |

## Build and verifier hygiene

Use /app/scripts/rebuild-chledger.sh for Go compile steps in the verifier flow. Reset workspace state with /app/scripts/reset-state.sh between cross-run checks.

Pytest under /tests drives chmutled through subprocess helpers in chledger_shell_ops.py and compares CLI artifacts to independent reference math in readiness_refmath.py. Export checks open the SQLite ledger at /app/output/chledger-rows.sqlite with the Python sqlite3 module. Hidden replica traps use TB3_FIXTURE_ROOT pointing at /opt/verifier-fixtures/chmutled_hidden.

Hardcoding /app/output artifacts or changing tests is insufficient.
