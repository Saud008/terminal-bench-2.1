# Collect and publish pipeline

## Reconcile

```
chmutled reconcile-partitions --metadata-dir <DIR> --mutations-dir <DIR> --replica-dir <DIR> --config-dir /app/fixtures/config --staging /app/state/chledger-staging.jsonl
```

Staging lines sorted by partition_id ascending, then mutation_version ascending.

Each staged object: mutation_id, partition_id, mutation_version, table_name, readiness_state, replica_lag_max, part_count, issued_at.

## Emit

```
chmutled emit-readiness --staging /app/state/chledger-staging.jsonl --sqlite /app/output/chledger-rows.sqlite --atlas /app/output/mutation-readiness-atlas.json
```

Repeated emit-readiness with identical staging must not duplicate SQLite rows for the same (partition_id, mutation_id) pair.

## Verifier fixture override

When TB3_FIXTURE_ROOT is set, reconcile-partitions reads metadata, mutations, and replica subdirectories from that root instead of bundled fixtures.
